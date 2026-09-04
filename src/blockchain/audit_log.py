"""
SwasthyaConnect — Blockchain Audit Logger
==========================================
Thin integration layer between database.py operations
and the blockchain engine.

Every call to these functions auto-creates a tamper-proof
blockchain record. No changes to existing function signatures needed.
"""

from src.blockchain.chain import (
    add_block,
    BLOCK_MEDICAL_RECORD,
    BLOCK_PRESCRIPTION,
    BLOCK_TREATMENT_UPDATE,
    BLOCK_REFERRAL_CREATED,
    BLOCK_AI_SUMMARY,
    BLOCK_AUTH_EVENT,
    BLOCK_RESOURCE_UPDATED,
    BLOCK_APPOINTMENT,
    compute_payload_hash,
)
import json


def log_medical_record(patient_id: int, record_type: str, title: str,
                       summary_json_str: str = None, actor_id: int = None):
    """
    Called when a new medical record is saved.
    Hashes the AI summary JSON as proof of what was stored.
    """
    payload = {
        "patient_id": patient_id,
        "record_type": record_type,
        "title": title,
    }
    # Include summary content hash if available
    if summary_json_str:
        try:
            summary = json.loads(summary_json_str)
            payload["diagnoses"] = summary.get("diagnosis", [])
            payload["vitals_hash"] = compute_payload_hash(summary.get("vitals", {}))
            payload["medications_count"] = len(summary.get("medications", []))
        except Exception:
            pass

    add_block(
        record_type=BLOCK_MEDICAL_RECORD,
        data=payload,
        patient_id=patient_id,
        actor_id=actor_id,
        extra_data=f"{record_type}: {title[:40]}"
    )


def log_prescription(patient_id: int, medicine_name: str,
                     dosage: str = None, frequency: str = None,
                     duration: str = None, actor_id: int = None):
    """Called when a prescription medicine row is saved."""
    payload = {
        "patient_id": patient_id,
        "medicine_name": medicine_name,
        "dosage": dosage,
        "frequency": frequency,
        "duration": duration,
    }
    add_block(
        record_type=BLOCK_PRESCRIPTION,
        data=payload,
        patient_id=patient_id,
        actor_id=actor_id,
        extra_data=f"Medicine: {medicine_name[:30]}"
    )


def log_treatment_update(patient_id: int, updated_by_id: int,
                         status: str, notes: str):
    """Called when a doctor logs a treatment status update."""
    payload = {
        "patient_id": patient_id,
        "updated_by": updated_by_id,
        "status": status,
        "notes_hash": compute_payload_hash(notes),  # hash notes, not store raw
    }
    add_block(
        record_type=BLOCK_TREATMENT_UPDATE,
        data=payload,
        patient_id=patient_id,
        actor_id=updated_by_id,
        extra_data=f"Status: {status}"
    )


def log_referral(patient_name: str, referred_by_id: int,
                 referred_to_id: int, reason: str):
    """Called when a doctor creates a referral."""
    payload = {
        "patient_name_hash": compute_payload_hash(patient_name),
        "referred_by": referred_by_id,
        "referred_to": referred_to_id,
        "reason": reason,
    }
    add_block(
        record_type=BLOCK_REFERRAL_CREATED,
        data=payload,
        patient_id=None,
        actor_id=referred_by_id,
        extra_data=f"Referral: {reason[:30]}"
    )


def log_auth_event(user_id: int, role: str, action: str = "LOGIN"):
    """Called on successful login/logout."""
    payload = {
        "user_id": user_id,
        "role": role,
        "action": action,
    }
    add_block(
        record_type=BLOCK_AUTH_EVENT,
        data=payload,
        patient_id=user_id if role == "patient" else None,
        actor_id=user_id,
        extra_data=f"{action}: {role}"
    )


def log_resource_update(hospital_id: int, hospital_name: str,
                        icu_total: int, icu_available: int,
                        oxygen_percent: int, status: str):
    """Called when hospital resources are updated."""
    payload = {
        "hospital_id": hospital_id,
        "hospital_name": hospital_name,
        "icu_total": icu_total,
        "icu_available": icu_available,
        "oxygen_percent": oxygen_percent,
        "status": status,
    }
    add_block(
        record_type=BLOCK_RESOURCE_UPDATED,
        data=payload,
        actor_id=hospital_id,
        extra_data=f"{hospital_name[:25]}: ICU {icu_available}/{icu_total}"
    )


def log_appointment(patient_id: int, doctor_id: int,
                    date_str: str, time_str: str):
    """Called when an appointment is booked."""
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "date": date_str,
        "time": time_str,
    }
    add_block(
        record_type=BLOCK_APPOINTMENT,
        data=payload,
        patient_id=patient_id,
        actor_id=patient_id,
        extra_data=f"Appt: {date_str} {time_str}"
    )


def log_grant_request(hospital_id: int, hospital_name: str, category: str, quantity: int, amount: float, reason: str):
    """Called when a hospital submits a resource/budget grant request to government."""
    from src.blockchain.chain import BLOCK_GRANT_REQUEST
    payload = {
        "hospital_id": hospital_id,
        "hospital_name": hospital_name,
        "category": category,
        "quantity": quantity,
        "requested_amount": amount,
        "reason": reason
    }
    add_block(
        record_type=BLOCK_GRANT_REQUEST,
        data=payload,
        actor_id=hospital_id,
        extra_data=f"Req {category}: ₹{amount:,.0f} ({hospital_name[:20]})"
    )


def log_govt_grant(request_id: int, hospital_name: str, category: str, approved_amount: float, status: str, govt_actor_id: int = 1):
    """Called when government approves/disburses funds for hospital resource grant."""
    from src.blockchain.chain import BLOCK_GRANT_DISBURSED
    payload = {
        "request_id": request_id,
        "hospital_name": hospital_name,
        "category": category,
        "approved_amount": approved_amount,
        "status": status
    }
    add_block(
        record_type=BLOCK_GRANT_DISBURSED,
        data=payload,
        actor_id=govt_actor_id,
        extra_data=f"Govt {status}: ₹{approved_amount:,.0f} for {hospital_name[:20]}"
    )
