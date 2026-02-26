import gspread
from google.oauth2.service_account import Credentials
import anthropic
import os

# Setup Google Sheets access
scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
gs_client = gspread.authorize(creds)

# Open your Google Sheet (name must match the linked sheet from your Google Form)
sheet = gs_client.open("Vedic Astro Submissions").sheet1

# Get all friend data
friends = sheet.get_all_records()

# Setup Claude
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_report(friend):
    prompt = f"""Generate a detailed Vedic astrology report for:
Name: {friend['Name']}
Birth Date: {friend['Birth Date']}
Birth Time: {friend['Birth Time']}
Birth Place: {friend['Birth Place']}

Include: Birth chart, planetary positions, dasha periods, yogas, and predictions."""

    message = claude.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


# Process all friends
for friend in friends:
    name = friend["Name"]
    filename = f"reports/{name.replace(' ', '_')}_astro_report.txt"

    if os.path.exists(filename):
        print(f"Skipping {name} (report already exists)")
        continue

    print(f"Generating report for {name}...")

    report = generate_report(friend)

    with open(filename, "w") as f:
        f.write(f"VEDIC ASTROLOGY REPORT\n")
        f.write(f"Name: {name}\n")
        f.write(f"Birth Date: {friend['Birth Date']}\n")
        f.write(f"Birth Time: {friend['Birth Time']}\n")
        f.write(f"Birth Place: {friend['Birth Place']}\n")
        f.write(f"{'=' * 60}\n\n")
        f.write(report)

    print(f"  Saved: {filename}")

print("\nDone!")
