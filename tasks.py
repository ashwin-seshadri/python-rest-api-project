import os
import requests
import jinja2
from dotenv import load_dotenv

load_dotenv()

domain = os.getenv("MAILGUN_DOMAIN")
apiKey = os.getenv("MAILGUN_API_KEY")

templates_loader = jinja2.FileSystemLoader("templates")
template_env = jinja2.Environment(loader=templates_loader)

def render_template(template_filename, **context):
    return template_env.get_template(template_filename).render(**context)

def send_simple_message(to, subject, body, html):
    return requests.post(
  		f"https://api.mailgun.net/v3/{domain}/messages",
  		auth=("api", apiKey),
  		data={"from": f"Mailgun Sandbox <postmaster@{domain}>",
			"to": to,
  			"subject": subject,
  			"text": body,
            "html": html
            })

def send_user_registration_email(email, username):
    return send_simple_message(
        email,
        "Sucessfully signed up",
        f"Hi {username}!, you have successfully signed up for flask-smorest rest-api store.",
        # code from action.html
        render_template("email/action.html", username=username)
    )