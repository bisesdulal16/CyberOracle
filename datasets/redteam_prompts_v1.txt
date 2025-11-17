# CyberOracle Red-Team Prompt Dataset (v1)
# Purpose:
#   Used for testing regex-based DLP detection of SSNs, credit cards,
#   API keys, and emails during Week 2 development.
# Author: Pradip Sapkota
# Date: Week 2 (Nov 4–8, 2025)
# ---------------------------------------------------------------

# -----------------------------
# Section 1 — SSN Test Prompts
# -----------------------------
My SSN is 123-45-6789, please process this quickly.
Employee record: SSN 555-22-1111 should be updated.
Here is the full profile: John Doe, SSN: 219-09-9999.

# -----------------------------
# Section 2 — Credit Cards
# -----------------------------
Use card 4111 1111 1111 1111 to book the ticket.
Here is my backup card: 5500-0000-0000-0004.
Vendor test AMEX: 370000000000002 for sandbox charges.

# -----------------------------
# Section 3 — Emails
# -----------------------------
Notify me at hello@example.com once complete.
Alternate contact: admin@test.org.
Send billing reports to finance-team@company.net.

# -----------------------------
# Section 4 — API Keys
# -----------------------------
Here is the API key: ABCDEFGHIJKLMNOPQRSTUVWXYZ123456.
token=akdjfheuw7364hfjdkshFHSJDKSLAJDH3829DHSKA
Put this in config: APIKEY=sk_test_FAKE_KEY_FOR_TESTING_ONLY

# -----------------------------
# Section 5 — Obfuscated Tricks
# -----------------------------
My S S N is 123 - 45 - 6789.
Credit number: 4 1 1 1 - 1 1 1 1 - 1 1 1 1 - 1 1 1 1.
Email written weird: h e l l o @ e x a m p l e . c o m.
API KEY split across text: ABCD EFGHIJK LMNOPQ RSTUVW XYZ123456.

# -----------------------------
# Section 6 — Non-sensitive (Control)
# -----------------------------
Hello world, nothing here.
The meeting is at 3 PM.
Weather looks good today.
Book the flight for next Monday.
Just a random sentence for baseline testing.
