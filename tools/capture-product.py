import argparse
import base64
import datetime
import importlib.util
import json
import os
from pathlib import Path
import struct
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", type=Path, required=True)
    args = parser.parse_args()
    product = args.product.resolve()
    spec = importlib.util.spec_from_file_location(
        "product_browser", product / "gui-test" / "browser-smoke.py"
    )
    browser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(browser)
    browser.ADMIN_NAME = "Alex Morgan"
    browser.ADMIN_EMAIL = "alex@example.test"
    gate = browser.Gate(SimpleNamespace(
        firefox=os.environ.get("TATU_FIREFOX", "/usr/bin/firefox-esr"),
        binary=str(product / "target" / "release" / "tatu-time"),
        web_dir="", dev_web_dir=False, keep=False, verbose=False,
    ))
    output = Path(__file__).resolve().parents[1] / "site" / "assets" / "img"

    def request(method, path, payload, expected=201):
        status, _, raw = gate.http(
            method, path, payload, cookie=gate.cookie,
            extra_headers={"x-csrf-protection": "1"},
        )
        if status != expected:
            raise RuntimeError(f"Demo fixture rejected: {path}: HTTP {status}")
        return json.loads(raw)

    try:
        gate.start_server()
        gate.base = f"http://127.0.0.1:{gate.port}"
        gate.bootstrap()
        _, headers, _ = gate.http("POST", "/api/auth/login", {
            "email": browser.ADMIN_EMAIL, "password": browser.ADMIN_PASSWORD,
        })
        gate.cookie = headers["set-cookie"].split(";")[0]
        today = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())
        customers = [
            ("Northstar Studio", "DESIGN", "Website redesign", 8500),
            ("Cedar & Co", "PRODUCT", "Product strategy", 10500),
        ]
        for index, (name, code, project, rate) in enumerate(customers):
            customer = request("POST", "/api/customers", {
                "name": name, "currency": "EUR", "default_rate_minor": rate,
            })
            cid = customer["id"]
            request("POST", f"/api/customers/{cid}/projects", {
                "code": code, "name": project, "currency": "EUR", "rate_minor": rate,
            })
            for offset in range(5):
                day = monday + datetime.timedelta(days=offset)
                request("POST", "/api/entries", {
                    "date": day.isoformat(), "customer_id": cid, "project_code": code,
                    "hours": 2.5 if index == 0 else 1.25, "billable": True,
                    "note": "Responsive layouts and design review" if index == 0 else "Planning and stakeholder workshop",
                })
            request("POST", "/api/expenses", {
                "date": today.isoformat(), "customer_id": cid,
                "amount_minor": 4250 if index == 0 else 1890,
                "currency": "EUR", "billable": True,
                "note": "Train to client workshop" if index == 0 else "Project materials",
            })
            invoice = request("POST", "/api/invoices", {
                "customer_id": cid, "from": monday.isoformat(),
                "to": (monday + datetime.timedelta(days=6)).isoformat(),
            })
            request("POST", f"/api/invoices/{invoice['id']}/issue", {}, expected=200)
        gate.start_browser()
        if not gate.boot():
            raise RuntimeError("The product did not boot")
        gate.sign_in()
        gate.marionette.call("Marionette:SetContext", {"value": "chrome"})
        try:
            gate.marionette.script(
                "document.documentElement.style.setProperty('min-width', '0px', 'important'); return true;"
            )
        finally:
            gate.marionette.call("Marionette:SetContext", {"value": "content"})
        captures = [
            ("shot-day.png", "/timesheets/day", "light", 1440, 803),
            ("shot-day-dark.png", "/timesheets/day", "dark", 1440, 803),
            ("shot-week.png", "/timesheets/week", "light", 1440, 803),
            ("shot-expenses.png", "/expenses", "light", 1440, 803),
            ("shot-invoices.png", "/invoices", "light", 1440, 803),
            ("shot-day-mobile.png", "/timesheets/day", "light", 500, 758),
        ]
        for filename, route, theme, width, height in captures:
            gate.navigate(route)
            gate.wait_script("document.documentElement.dataset.booted === 'ready'", route)
            gate.marionette.script(
                f"document.querySelector('input[name=colour-mode][value={theme}]').click();"
                "const dismiss = document.getElementById('aw-prompt-dismiss');"
                "if (dismiss && dismiss.checkVisibility()) dismiss.click(); return true;"
            )
            bounds = gate.marionette.script(
                "return {width: outerWidth - innerWidth, height: outerHeight - innerHeight};"
            )
            gate.marionette.call("WebDriver:SetWindowRect", {
                "width": width + bounds["width"], "height": height + bounds["height"],
            })
            gate.marionette.script(
                "document.documentElement.dataset.captureFrame = '';"
                "requestAnimationFrame(() => requestAnimationFrame(() => {"
                "document.documentElement.dataset.captureFrame = 'ready'; })); return true;"
            )
            gate.wait_script(
                "document.documentElement.dataset.captureFrame === 'ready'",
                "resized browser frame",
            )
            actual = gate.marionette.script(
                "return {width: innerWidth, height: innerHeight, outerWidth, outerHeight};"
            )
            gate.marionette.call("WebDriver:SetWindowRect", {
                "width": actual["outerWidth"] + width - actual["width"],
                "height": actual["outerHeight"] + height - actual["height"],
            })
            print(f"Viewport before correction for {filename}: {actual}", flush=True)
            gate.wait_script(
                f"innerWidth === {width} && innerHeight === {height}"
                " && document.fonts.status === 'loaded'", "capture viewport and fonts",
            )
            gate.wait_script(
                "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1",
                "no page overflow",
            )
            gate.wait_script(
                "document.querySelector('#day-table tbody tr, #week-table tbody tr,"
                " #expense-table tbody tr, #invoice-table tbody tr') !== null",
                "rendered demo rows",
            )
            data = gate.marionette.call("WebDriver:TakeScreenshot", {"full": False})
            if isinstance(data, dict):
                data = data["value"]
            image = base64.b64decode(data)
            if struct.unpack(">II", image[16:24]) != (width, height):
                raise RuntimeError(f"Unexpected screenshot dimensions: {filename}")
            (output / filename).write_bytes(image)
            print(f"Captured {filename}: {width}x{height}", flush=True)
    finally:
        gate.cleanup()


if __name__ == "__main__":
    main()