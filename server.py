from enum import Enum
from flask import Flask, request, jsonify
import meterbus
import re
from decimal import Decimal

app = Flask(__name__)


def get_medium_string(medium_value):
    medium_strings = {
        0x00: "Other",
        0x01: "Oil",
        0x02: "Electricity",
        0x03: "Gas",
        0x04: "Heat Out",
        0x05: "Steam",
        0x06: "Hot Water",
        0x07: "Water",
        0x08: "Heat Cost",
        0x09: "Compressed Air",
        0x0A: "Cool Out",
        0x0B: "Cool In",
        0x0C: "Heat In",
        0x0D: "Heat Cool",
        0x0E: "Bus",
        0x0F: "Unknown",
        0x10: "Irrigation",
        0x11: "Water Logger",
        0x12: "Gas Logger",
        0x13: "Gas Conversion",
        0x14: "Colorific",
        0x15: "Boil Water",
        0x16: "Cold Water",
        0x17: "Dual Water",
        0x18: "Pressure",
        0x19: "ADC",
        0x1A: "Smoke",
        0x1B: "Room Sensor",
        0x1C: "Gas Detector",
        0x20: "Breaker E",
        0x21: "Valve",
        0x25: "Customer Unit",
        0x28: "Waste Water",
        0x29: "Garbage",
        0x30: "Service Unit",
        0x36: "RC System",
        0x37: "RC Meter",
    }

    return medium_strings.get(medium_value, "Unknown")


def get_vif_unit_string(vif_unit_value):
    vif_unit_strings = {
        meterbus.VIFUnit.ENERGY_WH: "Energy (Wh)",
        meterbus.VIFUnit.ENERGY_J: "Energy (J)",
        meterbus.VIFUnit.VOLUME: "Volume",
        meterbus.VIFUnit.MASS: "Mass",
        meterbus.VIFUnit.ON_TIME: "On Time",
        meterbus.VIFUnit.OPERATING_TIME: "Operating Time",
        meterbus.VIFUnit.POWER_W: "Power (W)",
        meterbus.VIFUnit.POWER_J_H: "Power (J/h)",
        meterbus.VIFUnit.VOLUME_FLOW: "Volume Flow",
        meterbus.VIFUnit.VOLUME_FLOW_EXT: "Volume Flow Ext",
        meterbus.VIFUnit.VOLUME_FLOW_EXT_S: "Volume Flow Ext S",
        meterbus.VIFUnit.MASS_FLOW: "Mass Flow",
        meterbus.VIFUnit.FLOW_TEMPERATURE: "Flow Temperature",
        meterbus.VIFUnit.RETURN_TEMPERATURE: "Return Temperature",
        meterbus.VIFUnit.TEMPERATURE_DIFFERENCE: "Temperature Difference",
        meterbus.VIFUnit.EXTERNAL_TEMPERATURE: "External Temperature",
        meterbus.VIFUnit.PRESSURE: "Pressure",
        meterbus.VIFUnit.DATE: "Date",
        meterbus.VIFUnit.DATE_TIME_GENERAL: "Date Time General",
        meterbus.VIFUnit.UNITS_FOR_HCA: "Units for HCA",
        meterbus.VIFUnit.RES_THIRD_VIFE_TABLE: "Reserved Third VIFE Table",
        meterbus.VIFUnit.AVG_DURATION: "Average Duration",
        meterbus.VIFUnit.ACTUALITY_DURATION: "Actuality Duration",
        meterbus.VIFUnit.FABRICATION_NO: "Fabrication No",
        meterbus.VIFUnit.IDENTIFICATION: "Identification",
        meterbus.VIFUnit.ADDRESS: "Address",
        meterbus.VIFUnit.FIRST_EXT_VIF_CODES: "First Ext VIF Codes",
        meterbus.VIFUnit.VARIABLE_VIF: "Variable VIF",
        meterbus.VIFUnit.VIF_FOLLOWING: "VIF Following",
        meterbus.VIFUnit.SECOND_EXT_VIF_CODES: "Second Ext VIF Codes",
        meterbus.VIFUnit.THIRD_EXT_VIF_CODES_RES: "Third Ext VIF Codes Res",
        meterbus.VIFUnit.ANY_VIF: "Any VIF",
        meterbus.VIFUnit.MANUFACTURER_SPEC: "Manufacturer Specific",
    }

    return vif_unit_strings.get(vif_unit_value, "Unknown")


def get_function_type_string(function_type_value):
    function_type_strings = {
        meterbus.FunctionType.INSTANTANEOUS_VALUE: "Instantaneous Value",
        meterbus.FunctionType.MAXIMUM_VALUE: "Maximum Value",
        meterbus.FunctionType.MINIMUM_VALUE: "Minimum Value",
        meterbus.FunctionType.ERROR_STATE_VALUE: "Error State Value",
        meterbus.FunctionType.SPECIAL_FUNCTION: "Special Function",
        meterbus.FunctionType.SPECIAL_FUNCTION_FILL_BYTE: "Special Function Fill Byte",
        meterbus.FunctionType.MORE_RECORDS_FOLLOW: "More Records Follow",
    }

    return function_type_strings.get(function_type_value, "Unknown")


def fix_value(value):
    if isinstance(value, Decimal):
        # Check if decimal is an integer
        if value % 1 == 0:
            return int(value)
        else:
            return float(value)
    return value


def parse_record(record, index):
    ult, unit, typ = record._parse_vifx()
    dlen, enc = record.dib.length_encoding
    storage_number, tariff, device = record.dib.parse_dife()

    if isinstance(unit, meterbus.MeasureUnit):
        if unit == meterbus.MeasureUnit.NONE:
            unit = ""
        else:
            unit = unit.value

    value = record.parsed_value
    if type(value) == str:
        try:
            value = value.decode("unicode_escape")
        except AttributeError:
            pass

    if record.dib.function_type == meterbus.FunctionType.SPECIAL_FUNCTION:
        value = record._dataField.decodeRAW

    record = {
        "id": index,
        # "storage_number": storage_number,
        "function": get_function_type_string(record.dib.function_type),
        "type": get_vif_unit_string(typ),
        "value": fix_value(value),
        "unit": unit,
    }

    if tariff is not None:
        record["tariff"] = tariff

    if device is not None:
        record["device"] = device

    return record


def make_struct(frame):
    mbus_data = {
        "information": {},
        "records": [],
    }

    # check if attribute frame.body exists
    if hasattr(frame, "body"):
        frame = frame.body

    if hasattr(frame, "bodyHeader"):
        hdr = frame.bodyHeader
        mbus_data["information"] = {
            "id": hdr.id_nr_field.decodeBCD,
            "manufacturer": hdr.manufacturer_field.decodeManufacturer,
            "version": hdr.version_field.parts[0],
        }

        #        if hasattr(hdr, "ci_field"):
        #            mbus_data["information"]["ci_field"] = hdr.ci_field.parts[0]

        if hasattr(hdr, "device_field"):
            mbus_data["information"]["device_type"] = hdr.device_field.parts[0]

        if hasattr(hdr, "access_number"):
            mbus_data["information"]["access_number"] = hdr.access_number.parts[0]

        if hasattr(hdr, "status"):
            mbus_data["information"]["status"] = hdr.status.parts[0]

        if hasattr(hdr, "signature"):
            mbus_data["information"]["signature"] = (
                "".join(map(lambda x: "{:02x}".format(x), hdr.sig_field.parts)),
            )

        if hasattr(hdr, "medium_field"):
            mbus_data["information"]["medium"] = get_medium_string(
                hdr.measure_medium_field.parts[0]
            )

    records = []
    if hasattr(frame, "bodyPayload"):
        records = frame.bodyPayload.records
    elif hasattr(frame, "records"):
        records = frame.records

    mbus_data["records"] = [
        parse_record(record, index) for index, record in enumerate(records)
    ]

    return mbus_data


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

    return make_struct(frame)


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
