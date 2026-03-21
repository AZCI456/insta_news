# 🔮 UniMelb Club Oracle (Working Title)

> **The definitive guide to free food and club events at the University of Melbourne.**

Stop digging through buried Instagram stories and abandoned Discord servers. **Club Oracle** is a student-built project designed to aggregate campus life into a single, high-signal feed. No AI slop, no password fatigue—just the info you need to find the pizza and the people.

---

## 🖼️ Visual Preview

<table>
  <tr>
    <!-- Teaching note: <td> elements create columns in each table row. We'll place two images in adjacent cells. -->
    <td>
      <!-- Teaching note: Replace 'path/to/desktop.png' and alt text with your own screenshot filepath and description -->
      <img src="promo_images/landing_page.png" alt="Desktop dashboard screenshot" width="340" style="border-radius:10px; border: 1px solid #555;">
    </td>
    <td>
      <img src="promo_images/signups_page.png" alt="Club Preference Page" width="340" style="border-radius:10px; border: 1px solid #555;">
    </td>
  </tr>
  <tr>
    <!-- Teaching note: Text captions for each image to make the preview accessible and clear. -->
    <td align="center"><em>Desktop dashboard (dark, minimal retro UI)</em></td>
    <td align="center"><em>Club Preference Page</em></td>
  </tr>
</table>

---

## 🍕 1. Today’s Food Events

*Updated daily at 8:00 AM via SQL refresh.*

This table pulls directly from our `food_events` database to ensure you never miss a lunch.


| Time             | Club / Host                                            | Food                         | Location             |
| ---------------- | ------------------------------------------------------ | ---------------------------- | -------------------- |
| **12:00 – 2:00** | **Engineering Music Society** *BBQ on South Lawn*      | Sausage sizzle (veg options) | South Lawn           |
| **6:00 – 8:00**  | **International Students Collective** *Dumpling Night* | Dumplings + tea              | Union House, Level 2 |


---

## 🤖 2. The Digest Engine

Our model processes messy club announcements and outputs clean, structured data. This allows us to send you "Magic Link" emails that only contain the clubs you actually care about.

**Example Model Output (JSON):**

```json
{
  "club_id": "146",
  "display_header": {
    "name": "MUMS",
    "food_tag": "🟢 FREE FOOD WEDNESDAY"
  },
  "main_event": "Competition Maths Catch-up",
  "summary_text": "MUMS has announced a Competition Maths Catch-up on Wednesday, March 18th at 5:30 PM in Room 215, Peter Hall, which will include free pizza. Following this, a Womxn in Maths Coffee Catch-up is scheduled for Thursday, March 19th, from 1:30 PM to 2:30 PM at Castro's Kiosk, offering free coffee and card games.",
  "links": [
    {
      "label": "Register: Competition Maths Catch-up",
      "url": "https://www.instagram.com/p/DV3HCcYk0Tc/"
    },
    {
      "label": "Register: Womxn in Maths Coffee Catch-up",
      "url": "https://www.instagram.com/p/DV3HCcYk0Tc/"
    }
  ]
}
```

---

## 🛠️ Tech Stack & Security

This project is built to be "Professor-Approved" in terms of security. No corners cut.

- **Backend:** FastAPI
- **Styling:** Tailwind CSS (Slate-950 Palette)
- **Intelligence:** Gemini-powered ETL (Extract, Transform, Load)
- **Privacy:** Emails are stored **hashed + encrypted** (SHA256 & Fernet). No plain-text student data ever touches the disk.
- **Security:** Fuzzing for malicious input and Cloudflare integration pending.

---

## 🚧 The Roadmap (Planned Launch: April/May 2026)

I’m working on this daily to ensure it’s ready for the mid-sem/exam grind.

- **Final Branding:** Deciding between *UniChap*, *MeetPoint*, *UniFeed*, or *ClubPoint*.
- **Automated Pipeline:** Fully wiring the 8 AM table updates.
- **Email ETL:** Polishing the final delivery engine.
- **Reference Memory:** Integrating Gemini reference memory into responses.
- **Audit:** Final security sign-off from UniMelb faculty.
- **Hosting:** Get domain name and host properly.

---

## 🔒 A Note on Privacy

Built by a student, for students. We don’t want your passwords, and we don’t want your data. We just want you to get fed. 

**Built with ❤️ at UniMelb.**