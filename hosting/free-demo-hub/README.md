# Free demo hosting

Runs the four paused demos alongside NASA in its existing free CPU server slot.
Each app has an isolated Python environment, process and URL. The other running
Spaces and the original paused Spaces are retained.

`sources.json` pins complete Hugging Face source snapshots. Application files are
copied byte for byte during the image build and recorded in `source-checksums.json`.
Only the NASA deployment Dockerfile and new `_hosting/` files are uploaded.
No original application file or database file is deleted or overwritten.

The new URLs are under `https://vikrant892-nasa-space-challenge.hf.space`:

| Demo | Path |
|---|---|
| NASA Cosmic Keys | `/` |
| Credit Card Fraud | `/demos/fraud/` |
| Log Analyzer | `/demos/logs/` |
| Password Strength API | `/demos/password/` |
| Phishing Detection | `/demos/phishing/` |

The GitHub workflow first builds and tests the shared server, including browser
requests and Streamlit WebSockets, before uploading anything. A failed runtime
verification restores the original NASA Dockerfile. No paid hardware or extra
replicas are requested. Free Spaces can sleep after inactivity. Demo uploads and
SQLite history use ephemeral server storage; existing paused Spaces are retained,
and their runtime data is not copied or deleted by this deployment.
