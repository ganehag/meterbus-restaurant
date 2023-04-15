# Meter-Bus Restaurant

Welcome to the Meter-Bus Restaurant, where we serve you the tastiest M-Bus data in a JSON format!

## Overview

Meter-Bus Restaurant is a Python-based application that exposes a single API endpoint for converting M-Bus data. The API takes POST data in either hex-encoded (plain text) or binary M-Bus format and returns the interpreted data in a delicious JSON format.

## Features

- Easy-to-use REST API endpoint
- Supports hex-encoded and binary M-Bus data input
- Converts M-Bus data into human-readable JSON format

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ganehag/meterbus-restaurant.git
```

2. Navigate to the project directory:

```bash
cd meterbus-restaurant
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:

```bash
python server.py
```

2. Send a POST request to the API endpoint with your M-Bus data:

```bash
curl -X POST -H "Content-Type: application/octet-stream" --data-binary "@your-data-file" http://localhost:port/api/convert
```

3. Enjoy your freshly cooked JSON data!
