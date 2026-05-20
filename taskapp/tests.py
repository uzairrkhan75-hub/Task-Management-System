"""
Drivex test suite.

Run:  python manage.py test taskapp
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Cars, Mechanic, Task
from .rbac import (
    get_mechanic_profile,
    is_shop_manager,
    mechanic_tasks_queryset,
    resolve_shop_access_role,
)

User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_manager_group():
    group, _ = Group.objects.get_or_create(name='Manager')
    return group


def make_manager(username='manager', password='pass1234'):
    user = User.objects.create_user(username=username, password=password)
    user.groups.add(make_manager_group())
    return user


def make_mechanic_user(username='mech_user', password='pass1234'):
    user = User.objects.create_user(username=username, password=password)
    mechanic = Mechanic.objects.create(name='Test Mechanic', user=user)
    return user, mechanic


def make_car(reg='ABC-001'):
    return Cars.objects.create(
        registration_number=reg,
        make='Toyota',
        model='Corolla',
    )


def make_task(car, mechanic=None, status='pending', priority='medium',
              estimated_hours=None):
    return Task.objects.create(
        car=car,
        mechanic=mechanic,
        title='Brake service',
        status=status,
        priority=priority,
        estimated_hours=estimated_hours,
    )


# ===========================================================================
# 1. MODEL TESTS
# ===========================================================================

class MechanicModelTest(TestCase):

    def setUp(self):
        self.car = make_car()
        self.mechanic = Mechanic.objects.create(name='Ali')

    # --- is_busy ---

    def test_is_busy_false_when_no_tasks(self):
        self.assertFalse(self.mechanic.is_busy)

    def test_is_busy_true_with_open_task(self):
        make_task(self.car, mechanic=self.mechanic, status='pending')
        # is_busy queries the DB each time — no need to refresh_from_db
        self.assertTrue(self.mechanic.is_busy)

    def test_is_busy_false_when_only_completed_task(self):
        make_task(self.car, mechanic=self.mechanic, status='completed')
        self.assertFalse(self.mechanic.is_busy)

    # --- availability_status ---

    def test_availability_status_free(self):
        self.assertEqual(self.mechanic.availability_status, 'free')

    def test_availability_status_on_leave(self):
        self.mechanic.is_on_leave = True
        self.mechanic.save()
        self.assertEqual(self.mechanic.availability_status, 'on_leave')

    def test_availability_status_manually_busy(self):
        self.mechanic.is_manually_busy = True
        self.mechanic.save()
        self.assertEqual(self.mechanic.availability_status, 'busy')

    def test_on_leave_takes_priority_over_busy(self):
        self.mechanic.is_on_leave = True
        self.mechanic.is_manually_busy = True
        self.mechanic.save()
        self.assertEqual(self.mechanic.availability_status, 'on_leave')

    # --- str ---

    def test_str(self):
        self.assertEqual(str(self.mechanic), 'Ali')


class CarsModelTest(TestCase):

    def setUp(self):
        self.car = make_car('XYZ-999')

    def test_str(self):
        self.assertIn('XYZ-999', str(self.car))

    def test_repair_eta_none_when_no_tasks(self):
        self.assertIsNone(self.car.repair_eta)

    def test_repair_eta_returns_soonest_task_eta(self):
        later = timezone.now() + timedelta(hours=10)
        sooner = timezone.now() + timedelta(hours=2)
        t1 = Task.objects.create(car=self.car, title='T1')
        t2 = Task.objects.create(car=self.car, title='T2')
        # Bypass Task.save() ETA recalculation by using update()
        Task.objects.filter(pk=t1.pk).update(promised_completion_at=later)
        Task.objects.filter(pk=t2.pk).update(promised_completion_at=sooner)
        self.assertEqual(self.car.repair_eta, sooner)

    def test_repair_eta_ignores_completed_tasks(self):
        Task.objects.create(
            car=self.car, title='Done',
            promised_completion_at=timezone.now() + timedelta(hours=1),
            status='completed',
        )
        self.assertIsNone(self.car.repair_eta)

    def test_repair_eta_ignores_tasks_without_eta(self):
        Task.objects.create(car=self.car, title='No ETA')
        self.assertIsNone(self.car.repair_eta)


class TaskModelTest(TestCase):

    def setUp(self):
        self.car = make_car()
        self.mechanic = Mechanic.objects.create(name='Bob')

    # --- promised_completion_at auto-calc ---

    def test_promised_completion_set_from_estimated_hours(self):
        task = make_task(self.car, estimated_hours=3)
        self.assertIsNotNone(task.promised_completion_at)
        delta = task.promised_completion_at - task.created_at
        self.assertAlmostEqual(delta.total_seconds(), 3 * 3600, delta=5)

    def test_promised_completion_cleared_when_hours_removed(self):
        task = make_task(self.car, estimated_hours=2)
        task.estimated_hours = None
        task.save()
        self.assertIsNone(task.promised_completion_at)

    def test_no_eta_when_no_estimated_hours(self):
        task = make_task(self.car)
        self.assertIsNone(task.promised_completion_at)

    # --- is_overdue ---

    def test_is_overdue_false_when_no_eta(self):
        task = make_task(self.car)
        self.assertFalse(task.is_overdue)

    def test_is_overdue_false_when_eta_in_future(self):
        task = make_task(self.car, estimated_hours=100)
        self.assertFalse(task.is_overdue)

    def test_is_overdue_true_when_eta_passed(self):
        task = make_task(self.car)
        # Bypass Task.save() which recomputes promised_completion_at
        Task.objects.filter(pk=task.pk).update(
            promised_completion_at=timezone.now() - timedelta(hours=1)
        )
        task.refresh_from_db()
        self.assertTrue(task.is_overdue)

    def test_is_overdue_false_when_completed(self):
        task = make_task(self.car, status='completed')
        task.promised_completion_at = timezone.now() - timedelta(hours=1)
        task.save()
        self.assertFalse(task.is_overdue)

    # --- mechanic busy cleared on task assignment ---

    def test_save_clears_manually_busy_when_task_assigned(self):
        self.mechanic.is_manually_busy = True
        self.mechanic.save()
        make_task(self.car, mechanic=self.mechanic, status='pending')
        self.mechanic.refresh_from_db()
        self.assertFalse(self.mechanic.is_manually_busy)

    def test_save_does_not_clear_busy_for_completed_task(self):
        self.mechanic.is_manually_busy = True
        self.mechanic.save()
        make_task(self.car, mechanic=self.mechanic, status='completed')
        self.mechanic.refresh_from_db()
        # completed tasks do NOT clear the flag
        self.assertTrue(self.mechanic.is_manually_busy)

    def test_str(self):
        task = make_task(self.car)
        self.assertIn('Brake service', str(task))
        self.assertIn(self.car.registration_number, str(task))


# ===========================================================================
# 2. RBAC TESTS
# ===========================================================================

class RBACTest(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            'admin', password='adminpass'
        )
        self.manager = make_manager('mgr')
        self.mech_user, self.mechanic = make_mechanic_user('mech')
        self.plain_user = User.objects.create_user('plain', password='pass1234')

    def test_superuser_is_shop_manager(self):
        self.assertTrue(is_shop_manager(self.superuser))

    def test_group_member_is_shop_manager(self):
        self.assertTrue(is_shop_manager(self.manager))

    def test_mechanic_user_not_shop_manager(self):
        self.assertFalse(is_shop_manager(self.mech_user))

    def test_plain_user_not_shop_manager(self):
        self.assertFalse(is_shop_manager(self.plain_user))

    def test_resolve_role_manager(self):
        self.assertEqual(resolve_shop_access_role(self.manager), 'manager')

    def test_resolve_role_mechanic(self):
        self.assertEqual(resolve_shop_access_role(self.mech_user), 'mechanic')

    def test_resolve_role_none_for_plain_user(self):
        self.assertIsNone(resolve_shop_access_role(self.plain_user))

    def test_get_mechanic_profile_returns_mechanic(self):
        profile = get_mechanic_profile(self.mech_user)
        self.assertEqual(profile, self.mechanic)

    def test_get_mechanic_profile_returns_none_for_manager(self):
        self.assertIsNone(get_mechanic_profile(self.manager))

    def test_mechanic_tasks_queryset_scoped_to_own_tasks(self):
        car = make_car()
        own_task = make_task(car, mechanic=self.mechanic)
        other_mech = Mechanic.objects.create(name='Other')
        make_task(car, mechanic=other_mech)
        qs = mechanic_tasks_queryset(self.mech_user)
        self.assertIn(own_task, qs)
        self.assertEqual(qs.count(), 1)

    def test_mechanic_tasks_queryset_manager_sees_all(self):
        car = make_car()
        make_task(car, mechanic=self.mechanic)
        make_task(car)
        qs = mechanic_tasks_queryset(self.manager)
        self.assertEqual(qs.count(), 2)


# ===========================================================================
# 3. AUTHENTICATION VIEW TESTS
# ===========================================================================

class AuthViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.mech_user, self.mechanic = make_mechanic_user()

    def test_login_page_loads(self):
        r = self.client.get(reverse('login'))
        self.assertEqual(r.status_code, 200)

    def test_login_redirects_manager_to_home(self):
        r = self.client.post(
            reverse('login'),
            {'username': 'manager', 'password': 'pass1234'},
            follow=True,
        )
        self.assertRedirects(r, reverse('home'))

    def test_login_redirects_mechanic_to_task_list(self):
        r = self.client.post(
            reverse('login'),
            {'username': 'mech_user', 'password': 'pass1234'},
            follow=True,
        )
        self.assertRedirects(r, reverse('task_list'))

    def test_login_with_bad_credentials_stays_on_login(self):
        r = self.client.post(
            reverse('login'),
            {'username': 'manager', 'password': 'wrongpassword'},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Please enter a correct username')

    def test_unauthenticated_home_redirects_to_login(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_logout_works(self):
        self.client.force_login(self.manager)
        r = self.client.post(reverse('logout'), follow=True)
        self.assertEqual(r.status_code, 200)


# ===========================================================================
# 4. ACCESS CONTROL TESTS (manager-only vs mechanic-only pages)
# ===========================================================================

class AccessControlTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.mech_user, self.mechanic = make_mechanic_user()
        self.plain_user = User.objects.create_user('plain', password='pass1234')
        self.car = make_car()

    # Manager-only pages: 200 for manager, redirect (302) for mechanic
    # ShopManagerRequiredMixin redirects mechanics to task_list, not 403.

    def _assert_manager_only(self, url):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.mech_user)
        r = self.client.get(url)
        self.assertIn(r.status_code, (302, 403))

    def test_car_list_manager_only(self):
        self._assert_manager_only(reverse('car_list'))

    def test_mechanic_list_manager_only(self):
        self._assert_manager_only(reverse('mechanic_list'))

    def test_user_list_manager_only(self):
        self._assert_manager_only(reverse('shop_user_list'))

    def test_home_redirects_mechanic_to_task_list(self):
        self.client.force_login(self.mech_user)
        r = self.client.get(reverse('home'), follow=True)
        self.assertRedirects(r, reverse('task_list'))

    def test_plain_user_gets_logged_out_from_home(self):
        self.client.force_login(self.plain_user)
        r = self.client.get(reverse('home'), follow=True)
        self.assertRedirects(r, reverse('login'))

    def test_mechanic_can_access_task_list(self):
        self.client.force_login(self.mech_user)
        r = self.client.get(reverse('task_list'))
        self.assertEqual(r.status_code, 200)

    def test_unauthenticated_task_list_redirects(self):
        r = self.client.get(reverse('task_list'))
        self.assertEqual(r.status_code, 302)

    def test_customer_eta_requires_manager(self):
        self.client.force_login(self.mech_user)
        r = self.client.get(reverse('customer_eta'), follow=True)
        self.assertRedirects(r, reverse('task_list'))

    def test_customer_eta_accessible_for_manager(self):
        self.client.force_login(self.manager)
        r = self.client.get(reverse('customer_eta'))
        self.assertEqual(r.status_code, 200)


# ===========================================================================
# 5. CAR CRUD TESTS
# ===========================================================================

class CarCRUDTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.client.force_login(self.manager)

    def test_car_list_shows_cars(self):
        car = make_car('TEST-01')
        r = self.client.get(reverse('car_list'))
        self.assertContains(r, 'TEST-01')

    def test_car_create(self):
        r = self.client.post(
            reverse('car_create'),
            {'registration_number': 'NEW-99', 'make': 'Honda', 'model': 'Civic'},
            follow=True,
        )
        self.assertRedirects(r, reverse('car_list'))
        self.assertTrue(Cars.objects.filter(registration_number='NEW-99').exists())

    def test_car_create_duplicate_registration_fails(self):
        make_car('DUP-01')
        r = self.client.post(
            reverse('car_create'),
            {'registration_number': 'DUP-01', 'make': 'Ford', 'model': 'Focus'},
        )
        self.assertEqual(r.status_code, 200)  # stays on form
        self.assertEqual(Cars.objects.filter(registration_number='DUP-01').count(), 1)

    def test_car_update(self):
        car = make_car('UPD-01')
        r = self.client.post(
            reverse('car_update', args=[car.pk]),
            {'registration_number': 'UPD-01', 'make': 'Suzuki', 'model': 'Swift'},
            follow=True,
        )
        self.assertRedirects(r, reverse('car_list'))
        car.refresh_from_db()
        self.assertEqual(car.make, 'Suzuki')

    def test_car_delete(self):
        car = make_car('DEL-01')
        r = self.client.post(reverse('car_delete', args=[car.pk]), follow=True)
        self.assertRedirects(r, reverse('car_list'))
        self.assertFalse(Cars.objects.filter(pk=car.pk).exists())

    def test_car_delete_cascades_tasks(self):
        car = make_car('CAS-01')
        task = make_task(car)
        self.client.post(reverse('car_delete', args=[car.pk]))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())


# ===========================================================================
# 6. MECHANIC CRUD & AVAILABILITY TESTS
# ===========================================================================

class MechanicCRUDTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.client.force_login(self.manager)

    def test_mechanic_list_loads(self):
        Mechanic.objects.create(name='Kamran')
        r = self.client.get(reverse('mechanic_list'))
        self.assertContains(r, 'Kamran')

    def test_mechanic_create(self):
        r = self.client.post(
            reverse('mechanic_create'),
            {'name': 'Zain', 'specialization': 'Brakes', 'is_active': True},
            follow=True,
        )
        self.assertRedirects(r, reverse('mechanic_list'))
        self.assertTrue(Mechanic.objects.filter(name='Zain').exists())

    def test_mechanic_update(self):
        mech = Mechanic.objects.create(name='OldName')
        r = self.client.post(
            reverse('mechanic_update', args=[mech.pk]),
            {'name': 'NewName', 'is_active': True},
            follow=True,
        )
        self.assertRedirects(r, reverse('mechanic_list'))
        mech.refresh_from_db()
        self.assertEqual(mech.name, 'NewName')

    def test_mechanic_delete(self):
        mech = Mechanic.objects.create(name='ToDelete')
        r = self.client.post(
            reverse('mechanic_delete', args=[mech.pk]), follow=True
        )
        self.assertRedirects(r, reverse('mechanic_list'))
        self.assertFalse(Mechanic.objects.filter(pk=mech.pk).exists())


class MechanicAvailabilityTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.client.force_login(self.manager)
        self.mechanic = Mechanic.objects.create(name='Avail Test')
        self.car = make_car()

    def _set_avail(self, value, follow=True):
        return self.client.post(
            reverse('mechanic_set_availability', args=[self.mechanic.pk]),
            {'availability': value},
            follow=follow,
        )

    def test_set_on_leave(self):
        self._set_avail('on_leave')
        self.mechanic.refresh_from_db()
        self.assertTrue(self.mechanic.is_on_leave)

    def test_set_manually_busy(self):
        self._set_avail('busy')
        self.mechanic.refresh_from_db()
        self.assertTrue(self.mechanic.is_manually_busy)

    def test_set_free_when_no_tasks(self):
        self.mechanic.is_manually_busy = True
        self.mechanic.save()
        self._set_avail('free')
        self.mechanic.refresh_from_db()
        self.assertFalse(self.mechanic.is_manually_busy)

    def test_set_free_with_open_tasks_shows_warning(self):
        make_task(self.car, mechanic=self.mechanic, status='pending')
        r = self._set_avail('free', follow=True)
        msgs = list(r.context['messages'])
        self.assertTrue(any('open tasks' in str(m) for m in msgs))
        self.mechanic.refresh_from_db()
        self.assertFalse(self.mechanic.is_on_leave)

    def test_mechanic_not_manager_gets_403(self):
        mech_user_obj, _ = make_mechanic_user('mech2')
        self.client.force_login(mech_user_obj)
        r = self._set_avail('busy', follow=False)
        self.assertEqual(r.status_code, 403)


# ===========================================================================
# 7. TASK CRUD & INLINE ACTION TESTS
# ===========================================================================

class TaskCRUDTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.client.force_login(self.manager)
        self.car = make_car()
        self.mechanic = Mechanic.objects.create(name='Worker')

    def test_task_list_shows_tasks(self):
        Task.objects.create(car=self.car, title='Oil change')
        r = self.client.get(reverse('task_list'))
        self.assertContains(r, 'Oil change')

    def test_task_create(self):
        r = self.client.post(
            reverse('task_create'),
            {
                'title': 'Tyre rotation',
                'car': self.car.pk,
                'status': 'pending',
                'priority': 'low',
                'description': '',
            },
            follow=True,
        )
        self.assertRedirects(r, reverse('task_list'))
        self.assertTrue(Task.objects.filter(title='Tyre rotation').exists())

    def test_task_create_with_estimated_hours_sets_eta(self):
        self.client.post(
            reverse('task_create'),
            {
                'title': 'ETA Task',
                'car': self.car.pk,
                'status': 'pending',
                'priority': 'medium',
                'estimated_hours': '5',
                'description': '',
            },
        )
        task = Task.objects.get(title='ETA Task')
        self.assertIsNotNone(task.promised_completion_at)

    def test_task_update(self):
        task = make_task(self.car)
        r = self.client.post(
            reverse('task_update', args=[task.pk]),
            {
                'title': 'Updated title',
                'car': self.car.pk,
                'status': 'in_progress',
                'priority': 'high',
                'description': '',
            },
            follow=True,
        )
        self.assertRedirects(r, reverse('task_list'))
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated title')
        self.assertEqual(task.status, 'in_progress')

    def test_task_delete(self):
        task = make_task(self.car)
        r = self.client.post(
            reverse('task_delete', args=[task.pk]), follow=True
        )
        self.assertRedirects(r, reverse('task_list'))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())


class TaskInlineActionsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.mech_user, self.mechanic = make_mechanic_user()
        self.car = make_car()
        self.task = make_task(self.car, mechanic=self.mechanic)

    def _set_status(self, user, status):
        self.client.force_login(user)
        return self.client.post(
            reverse('task_set_status', args=[self.task.pk]),
            {'status': status},
            follow=True,
        )

    def _set_priority(self, user, priority):
        self.client.force_login(user)
        return self.client.post(
            reverse('task_set_priority', args=[self.task.pk]),
            {'priority': priority},
            follow=True,
        )

    def test_manager_can_set_status(self):
        self._set_status(self.manager, 'in_progress')
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')

    def test_manager_can_set_priority(self):
        self._set_priority(self.manager, 'high')
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, 'high')

    def test_assigned_mechanic_can_change_status(self):
        self._set_status(self.mech_user, 'completed')
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')

    def test_unassigned_mechanic_cannot_change_status(self):
        other_user = User.objects.create_user('other_mech', password='pass1234')
        Mechanic.objects.create(name='Other Mechanic', user=other_user)
        self.client.force_login(other_user)
        r = self.client.post(
            reverse('task_set_status', args=[self.task.pk]),
            {'status': 'completed'},
        )
        self.assertEqual(r.status_code, 403)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'pending')

    def test_invalid_status_shows_error(self):
        self.client.force_login(self.manager)
        r = self.client.post(
            reverse('task_set_status', args=[self.task.pk]),
            {'status': 'banana'},
            follow=True,
        )
        msgs = list(r.context['messages'])
        self.assertTrue(any('Invalid' in str(m) for m in msgs))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'pending')

    def test_set_status_requires_post(self):
        self.client.force_login(self.manager)
        r = self.client.get(reverse('task_set_status', args=[self.task.pk]))
        self.assertEqual(r.status_code, 405)

    def test_set_priority_requires_post(self):
        self.client.force_login(self.manager)
        r = self.client.get(reverse('task_set_priority', args=[self.task.pk]))
        self.assertEqual(r.status_code, 405)


# ===========================================================================
# 8. CUSTOMER ETA LOOKUP TEST
# ===========================================================================

class CustomerEtaTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.client.force_login(self.manager)
        self.car = make_car('LOOKUP-01')

    def test_search_existing_car(self):
        r = self.client.get(
            reverse('customer_eta'),
            {'registration_number': 'LOOKUP-01'},
        )
        self.assertContains(r, 'LOOKUP-01')
        self.assertIsNone(r.context.get('lookup_error'))

    def test_search_case_insensitive(self):
        r = self.client.get(
            reverse('customer_eta'),
            {'registration_number': 'lookup-01'},
        )
        self.assertContains(r, 'LOOKUP-01')

    def test_search_missing_car_shows_error(self):
        r = self.client.get(
            reverse('customer_eta'),
            {'registration_number': 'NOTEXIST-99'},
        )
        self.assertIsNotNone(r.context.get('lookup_error'))
        self.assertContains(r, 'No car found')

    def test_blank_search_shows_no_error(self):
        r = self.client.get(reverse('customer_eta'))
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.context.get('lookup_error'))


# ===========================================================================
# 9. DASHBOARD STATS TEST
# ===========================================================================

class DashboardTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = make_manager()
        self.client.force_login(self.manager)
        self.car = make_car()

    def test_dashboard_counts_active_tasks(self):
        make_task(self.car, status='pending')
        make_task(self.car, status='in_progress')
        make_task(self.car, status='completed')
        r = self.client.get(reverse('home'))
        self.assertEqual(r.context['active_tasks'], 2)

    def test_dashboard_counts_overdue(self):
        task = make_task(self.car)
        Task.objects.filter(pk=task.pk).update(
            promised_completion_at=timezone.now() - timedelta(hours=1)
        )
        r = self.client.get(reverse('home'))
        self.assertEqual(r.context['overdue_tasks'], 1)

    def test_dashboard_counts_due_soon(self):
        task = make_task(self.car)
        Task.objects.filter(pk=task.pk).update(
            promised_completion_at=timezone.now() + timedelta(hours=12)
        )
        r = self.client.get(reverse('home'))
        self.assertEqual(r.context['due_soon'], 1)

    def test_dashboard_total_cars(self):
        make_car('C1')
        make_car('C2')
        r = self.client.get(reverse('home'))
        self.assertGreaterEqual(r.context['total_cars'], 2)
