from flask import Flask, request, jsonify
import meterbus
import re
from decimal import Decimal

app = Flask(__name__)


def fix_values(record):
    if "value" in record and isinstance(record["value"], Decimal):
        # Check if decimal is an integer
        if record["value"] % 1 == 0:
            record["value"] = int(record["value"])
        else:
            record["value"] = float(record["value"])
    return record


def fix_records(data):
    if data["body"] and data["body"]["records"]:
        records = data["body"]["records"]
        data["body"]["records"] = list(map(fix_values, records))

    return data


def process_mbus_data(data):
    try:
        frame = meterbus.load(data)
    except meterbus.MBusFrameDecodeError:
        frame = None

    if frame is None:
        try:
            tbody = meterbus.TelegramBody()
            frame = tbody.load(data)
        except meterbus.MBusFrameDecodeError as e:
            raise Exception(f"Error loading M-Bus data: {e}")

    if frame is None:
        raise Exception("Error loading M-Bus data")

    return fix_records(frame.interpreted)


@app.route("/api/convert", methods=["POST"])
def convert():
    if request.content_type == "text/plain":
        # remove whitespace and newlines
        input_data = request.get_data().decode("utf-8")
        input_data = input_data.strip().replace("\n", "")
        input_data = map(lambda x: int(x, 16), re.findall("..", input_data))
        input_data = list(input_data)
    elif request.content_type == "application/octet-stream":
        input_data = request.get_data()
    else:
        return jsonify({"error": "Invalid content type"}), 400

    if not input_data:
        return jsonify({"error": "No data provided"}), 400

    try:
        json_data = process_mbus_data(input_data)
    except Exception as e:
        return jsonify({"error": f"Error processing M-Bus data: {e}"}), 500

    return jsonify(json_data)


if __name__ == "__main__":
    app.run()
