"""Pruebas unitarias del control local de admisión."""

import pytest

from src.core.admission import AdmissionController, AdmissionPermit


def test_acquires_permits_up_to_capacity():
    admission = AdmissionController(capacity=2)

    first = admission.try_acquire()
    second = admission.try_acquire()

    assert first is not None
    assert second is not None
    assert first is not second
    assert admission.in_use == 2
    assert admission.in_use <= admission.capacity


def test_rejects_acquisition_immediately_at_capacity():
    admission = AdmissionController(capacity=1)
    permit = admission.try_acquire()

    assert permit is not None
    assert admission.try_acquire() is None
    assert admission.in_use == 1


def test_release_allows_a_new_acquisition():
    admission = AdmissionController(capacity=1)
    first = admission.try_acquire()

    assert first is not None
    first.release()

    second = admission.try_acquire()
    assert second is not None
    assert second is not first
    assert admission.in_use == 1


def test_releasing_the_same_permit_repeatedly_changes_count_once():
    admission = AdmissionController(capacity=2)
    permit = admission.try_acquire()

    assert permit is not None
    permit.release()
    permit.release()
    permit.release()

    assert permit.released
    assert admission.in_use == 0
    assert admission.in_use >= 0


def test_ungranted_permit_cannot_release_a_legitimate_permit():
    admission = AdmissionController(capacity=1)
    legitimate = admission.try_acquire()
    assert legitimate is not None

    with pytest.raises(TypeError):
        AdmissionPermit(admission)

    assert admission.in_use == 1
    assert not legitimate.released

    legitimate.release()
    assert legitimate.released
    assert admission.in_use == 0


def test_rejects_acquisitions_when_closed_and_reopens():
    admission = AdmissionController(capacity=1)
    existing = admission.try_acquire()
    assert existing is not None

    admission.close()
    assert not admission.accepting
    assert admission.try_acquire() is None
    assert admission.in_use == 1

    admission.reopen()
    assert admission.accepting
    assert admission.try_acquire() is None  # El permiso previo sigue ocupado.

    existing.release()
    new_permit = admission.try_acquire()
    assert new_permit is not None
    assert admission.in_use == 1


def test_permit_acquired_before_close_can_be_released_after_close():
    admission = AdmissionController(capacity=1)
    permit = admission.try_acquire()
    assert permit is not None

    admission.close()
    permit.release()

    assert permit.released
    assert admission.in_use == 0


def test_inconsistent_release_at_zero_raises_without_negative_count():
    admission = AdmissionController(capacity=1)
    permit = admission.try_acquire()
    assert permit is not None
    permit.release()

    with pytest.raises(RuntimeError, match="No hay permisos ocupados"):
        admission._release_permit(permit)

    assert admission.in_use == 0
    assert admission.in_use >= 0


def test_context_manager_releases_permit_after_exception():
    admission = AdmissionController(capacity=1)

    with pytest.raises(RuntimeError, match="fallo de prueba"):
        with admission.try_acquire() as permit:
            assert permit is not None
            assert admission.in_use == 1
            raise RuntimeError("fallo de prueba")

    assert permit.released
    assert admission.in_use == 0
    assert admission.in_use <= admission.capacity


@pytest.mark.parametrize("capacity", [0, -1])
def test_rejects_non_positive_capacity(capacity):
    with pytest.raises(ValueError, match="positivo"):
        AdmissionController(capacity=capacity)


@pytest.mark.parametrize("capacity", [True, False, 1.5, "2", None])
def test_rejects_capacity_that_is_not_an_integer(capacity):
    with pytest.raises(TypeError, match="entero"):
        AdmissionController(capacity=capacity)
