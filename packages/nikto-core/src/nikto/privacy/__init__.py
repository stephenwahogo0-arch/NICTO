"""NIKTO Privacy Policy — full disclosure of data practices, user rights, and safety commitments."""
from datetime import datetime


PRIVACY_POLICY_VERSION = "1.0.0"
PRIVACY_POLICY_DATE = "May 20, 2026"


PRIVACY_POLICY_TEXT = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    NIKTO PRIVACY POLICY                         ║
║                       Version {PRIVACY_POLICY_VERSION}                        ║
║                    Effective: {PRIVACY_POLICY_DATE}                    ║
╚══════════════════════════════════════════════════════════════════╝

At NIKTO, your privacy and safety are our highest priorities.
This policy explains how we collect, use, store, and protect your data.

────────────────────────────────────────────────────────────────

1. DATA WE COLLECT
────────────────────────────────────────────────────────────────

   a) INFORMATION YOU PROVIDE:
      • Full name
      • Mobile phone number (required for identity verification)
      • Email address (for account recovery and security alerts)
      • Country / region of residence
      • Emergency contact name and phone number
      • Age confirmation (you must be 18 or older)

   b) INFORMATION COLLECTED AUTOMATICALLY:
      • Device ID (unique machine identifier — not your serial number)
      • Operating system and version
      • Session timestamps and duration
      • Command and interaction logs (for safety auditing)
      • Error reports and crash data
      • Anonymized usage statistics

   c) SENSITIVE DATA WE DO NOT COLLECT:
      • Passwords, credit card numbers, or financial account details
      • Private keys (wallet keys are generated locally and never shared)
      • Biometric data (fingerprints, face scans)
      • Precise geolocation (only country-level)
      • Browsing history outside NIKTO

────────────────────────────────────────────────────────────────

2. HOW WE STORE YOUR DATA
────────────────────────────────────────────────────────────────

   • All data is stored LOCALLY on your machine under ~/.nikto/
   • The registry database is ENCRYPTED using AES-256-GCM
   • Encryption keys are derived from your machine's unique identity
     — your data cannot be read if moved to another machine
   • Logs are stored in an append-only format to prevent tampering
   • Backups are never transmitted to external servers

────────────────────────────────────────────────────────────────

3. HOW WE USE YOUR DATA
────────────────────────────────────────────────────────────────

   • To verify your identity and prevent unauthorized access
   • To enable emergency contact and safety features
   • To audit system usage for abuse detection and prevention
   • To comply with legal and law enforcement obligations
   • To improve NIKTO's performance and reliability

   YOUR DATA IS NEVER:
   • Sold to third parties (NIKTO is not a commercial product)
   • Used for advertising or marketing
   • Shared with data brokers or analytics companies
   • Transmitted without your explicit consent

────────────────────────────────────────────────────────────────

4. DATA SHARING AND DISCLOSURE
────────────────────────────────────────────────────────────────

   NIKTO will only share your data in the following circumstances:

   a) WITH YOUR EXPLICIT CONSENT:
      • You may opt-in to share anonymized usage data for research
      • You may request data export at any time

   b) FOR EMERGENCY SERVICES:
      • If you trigger the SOS/emergency feature, your emergency
        contact information and last known session activity may be
        shared with emergency services or your designated contact

   c) FOR LAW ENFORCEMENT (POLICE COOPERATION):
      • NIKTO includes a Police Cooperation Mode that, when
        presented with a valid legal order (warrant, subpoena, or
        equivalent), can export complete activity logs for
        law enforcement investigation
      • All data exports are timestamped and logged
      • You will be notified unless prohibited by law

────────────────────────────────────────────────────────────────

5. SAFETY AND POLICE FEATURES
────────────────────────────────────────────────────────────────

   a) ACTIVITY AUDIT LOG:
      • Every command and significant action is timestamped and logged
      • Logs are append-only and cannot be modified after creation
      • Logs can be exported for safety reviews or police investigations

   b) ABUSE REPORTING:
      • Built-in mechanism to report abusive behavior
      • Reports include context, timestamps, and relevant session data
      • Reports are stored securely and can be forwarded to authorities

   c) EMERGENCY / SOS SYSTEM:
      • Register an emergency contact during onboarding
      • Trigger SOS mode to alert your contact with your session info
      • SOS can be triggered via a safety keyword or external signal

   d) POLICE COOPERATION MODE:
      • Complete audit log export with cryptographic integrity verification
      • Chain-of-custody tracking for all exported evidence
      • Compliance with lawful data requests
      • Tamper-evident logging ensures exported data is verifiable

   e) SAFETY LOCK:
      • Optional PIN protection for NIKTO access
      • Prevents unauthorized use of your system
      • Locks automatically after inactivity

   f) CONTENT SAFETY:
      • NIKTO monitors for potentially dangerous or illegal content
      • Suspicious activity is flagged and logged
      • You will be warned before executing high-risk operations

────────────────────────────────────────────────────────────────

6. YOUR RIGHTS
────────────────────────────────────────────────────────────────

   As a NIKTO user, you have the following rights:

   a) RIGHT TO KNOW:
      • You have the right to know what data we collect and why
      • This policy serves as that disclosure

   b) RIGHT TO ACCESS:
      • You may request a full export of your data at any time
      • Use the /privacy command or run: nikto privacy export

   c) RIGHT TO RECTIFICATION:
      • You may update your registration information at any time
      • Use: nikto register --update

   d) RIGHT TO DELETION ("RIGHT TO BE FORGOTTEN"):
      • You may delete all stored data at any time
      • Use: nikto privacy delete-data
      • This will remove your registration, logs, and all associated data
      • NOTE: Audit logs required by law may be retained in a sealed format

   e) RIGHT TO WITHDRAW CONSENT:
      • You may withdraw consent at any time
      • Withdrawal will deactivate certain features (emergency contact, etc.)
      • Core NIKTO functionality will continue to work

   f) RIGHT TO DATA PORTABILITY:
      • Your data can be exported in a machine-readable format (JSON)
      • Use: nikto privacy export --format json

────────────────────────────────────────────────────────────────

7. DATA RETENTION
────────────────────────────────────────────────────────────────

   • Activity logs: Retained for the lifetime of the installation
     or until you request deletion
   • Registration data: Retained until deletion is requested
   • Emergency contact info: Retained until you remove it or delete your account
   • Anonymized statistics: Retained indefinitely for system improvement
   • Logs subject to legal hold: Retained as required by applicable law

────────────────────────────────────────────────────────────────

8. SECURITY MEASURES
────────────────────────────────────────────────────────────────

   • All stored data is encrypted at rest (AES-256-GCM)
   • Registry database uses authenticated encryption
   • Activity logs are append-only with integrity checks
   • NIKTO never transmits data over the network without explicit consent
   • The system does not contain backdoors or surveillance capabilities
   • Data is stored on your local machine only
   • No cloud storage, no remote servers, no third-party processing

────────────────────────────────────────────────────────────────

9. CHILDREN'S PRIVACY
────────────────────────────────────────────────────────────────

   • NIKTO is not intended for users under 18 years of age
   • We require age confirmation during registration
   • If we discover a user is under 18, their data will be deleted
   • We do not knowingly collect data from minors

────────────────────────────────────────────────────────────────

10. CHANGES TO THIS POLICY
────────────────────────────────────────────────────────────────

    • This policy may be updated as NIKTO evolves
    • You will be notified of material changes on next startup
    • Continued use after changes constitutes acceptance
    • Previous versions of this policy are stored locally for reference

────────────────────────────────────────────────────────────────

11. CONTACT AND COMPLIANCE
────────────────────────────────────────────────────────────────

    For privacy concerns, data requests, or safety issues:
    • Use the built-in command: nikto privacy contact
    • Report abuse: nikto safety report-abuse
    • Emergency: Use the SOS feature in NIKTO

    This system is designed to comply with:
    • General Data Protection Regulation (GDPR)
    • California Consumer Privacy Act (CCPA)
    • Applicable local data protection laws

────────────────────────────────────────────────────────────────

12. CONSENT
────────────────────────────────────────────────────────────────

    BY USING NIKTO, YOU ACKNOWLEDGE THAT YOU HAVE READ,
    UNDERSTOOD, AND AGREE TO THIS PRIVACY POLICY.

    You consent to:
    • The collection and storage of the data described above
    • The use of your data for safety, audit, and legal compliance
    • The emergency and police cooperation features described herein

    You may withdraw consent at any time by deleting your data.
    (nikto privacy delete-data)

────────────────────────────────────────────────────────────────

© {datetime.now().year} NIKTO AI System. All rights reserved.
"""


def get_privacy_policy():
    return PRIVACY_POLICY_TEXT


def get_policy_summary():
    return """NIKTO stores your data LOCALLY and ENCRYPTED. Key points:
  • Phone number required for identity verification & emergency contact
  • All data stored on YOUR machine — never transmitted without consent
  • Activity logs kept for safety — exportable for police cooperation
  • You can access, export, or delete all your data at any time
  • No selling, no ads, no cloud storage, no surveillance
"""
