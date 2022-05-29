# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
import board
import busio
import displayio
import neopixel
import terminalio
import json
import time

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
    
# constants
font = bitmap_font.load_font('lib/5x7.bdf')
char_width = 5
char_height = 7  
board_width = 64
board_height = 32
number_trains = 3

# set up matrix
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel = board.NEOPIXEL, debug=False)
group = displayio.Group()

# fetch data from metro API
def fetchData(network):
    metro_api = "https://api.wmata.com/StationPrediction.svc/json/GetPrediction/"
    station_name = "K01"
    
    r = network.fetch_data(
        metro_api + station_name,
        headers={"api_key": secrets["api_key"]},
        json_path=([],)
    )
    return r.get('Trains')
    
# coordinate a line string with a color
# (orange or silver)
def get_line_color(line_string):
    if line_string == 'OR':
        return 0xFF5500
    return 0xAAAAAA

# display header ("LN DEST MIN")
def displayHeader():
    y = 4
    line_x = 1
    destination_x = 1 + (char_width * 3)
    minutes_x = board_width - (char_width * 3)
    heading_color = 0xFF0000

    line = Label(
        font,
        color = heading_color,
        text='LN'
    )
    line.y = y
    line.x = line_x

    destination = Label(
        font,
        color = heading_color,
        text='DEST'
    )
    destination.y = y
    destination.x = destination_x

    minutes = Label(
        font,
        color = heading_color,
        text='MIN'
    )
    minutes.y = y
    minutes.x = minutes_x

    group.append(line)
    group.append(destination)
    group.append(minutes)

    return

# load the template footer line 
def loadFooter():
    y = board_height - 1
    x = 1
    footer_color = 0x0000FF
    dot_color = 0xFF0000
    station_color = 0x00FF00

    footer = Rect(
        x,
        y,
        board_width - x,
        1,
        fill = footer_color
    )

    station = Rect(
        30,
        y,
        4,
        1,
        fill = station_color
    )

    east_1 = Rect(
        5,
        y,
        1,
        1,
        fill = dot_color
    )

    east_2 = Rect(
        5,
        y,
        1,
        1,
        fill = dot_color
    )

    west_1 = Rect(
        5,
        y,
        1,
        1,
        fill = dot_color
    )

    west_2 = Rect(
        5,
        y,
        1,
        1,
        fill = dot_color
    )

    group.append(footer)
    group.append(station)
    footer_features = [east_1, east_2, west_1, west_2]
    for i in footer_features:
        group.append(i)
    return footer_features

# load the template body data
def loadBody():
    lines = []

    line_x = 1
    destination_x = 1 + char_width
    minutes_x = board_width - (char_width * 3)
    text_color = 0xFF7500

    for index in range(number_trains):
        y = (4 + char_height) + (char_height * index)
        line_color = 0xAAAAAA

        line = Rect(
            line_x,
            y - 3,
            2,
            6,
            fill = line_color
        )

        destination = Label(
            font,
            color=text_color,
            text='LOADING'
        )
        destination.y = y
        destination.x = destination_x

        minutes = Label(
            font,
            color=text_color,
            text='0'
        )
        minutes.y = y
        minutes.x = minutes_x

        group.append(line)
        group.append(destination)
        group.append(minutes)
        lines.append((line, destination, minutes))

    return lines

# update the body data with arriving trains
def updateBody(data, lines):
    assert(len(data) == len(lines))
    
    max_destination_chars = 8
    max_time_chars = 3

    for index, t in enumerate(data):
        assert(len(lines[index]) == 3)

        lines[index][0].fill = get_line_color(t.get('Line'))
        lines[index][1].text = t.get('Destination').split(' ')[0][:max_destination_chars]
        lines[index][2].text = t.get('Min')[:max_time_chars]

    return

# update the footer with arriving trains
def updateFooter(data, footer_features):
    west_stations = ["K02", "K03", "K04", "K05", "K06", "K07", "K08", "N01", "N02", "N03", "N04", "N06"]
    east_updates = []
    west_updates = []

    for index, t in enumerate(data):
        if not t.get('DestionationCode') and ('Wiehle' in t.get('Destination') or 'Vienna' in t.get('Destination')):
            t['DestinationCode'] = 'N06'
        elif not t.get('DestinationCode') and ('New' in t.get('Destination') or 'Largo' in t.get('Destination')):
            t['DestinationCode'] = 'east'

        if t.get('Min') and t.get('Line'):
            if len(east_updates) < 2 and t.get('DestinationCode') not in west_stations:
                if t.get('Min').isdigit():
                    east_updates.append((min(30, int(t.get("Min"))), t.get('Line')))
                elif t.get('Min') in ['BRD', 'ARR']:
                    east_updates.append((len(east_updates), t.get('Line')))
            elif len(west_updates) < 2 and t.get('DestinationCode') in west_stations:
                if t.get('Min').isdigit():
                    west_updates.append((min(30, int(t.get("Min"))), t.get('Line')))
                elif t.get('Min') in ['BRD', 'ARR']:
                    west_updates.append((len(west_updates), t.get('Line')))
            else:
                print("cannot identify", t)

    if 1 <= len(east_updates):
        footer_features[0].x = 30-east_updates[0][0]
        footer_features[0].fill = get_line_color(east_updates[0][1])
    else:
        footer_features[0].x=0

    if 2 <= len(east_updates):
        footer_features[1].x= 30-east_updates[1][0]
        footer_features[1].fill = get_line_color(east_updates[1][1])
    else:
        footer_features[1].x=0

    if 1 <= len(west_updates):
        footer_features[2].x = 34+west_updates[0][0]
        footer_features[2].fill = get_line_color(west_updates[0][1])
    else:
        footer_features[2].x=0
    if 2 <= len(west_updates):
        footer_features[3].x= 34+west_updates[1][0]
        footer_features[3].fill = get_line_color(west_updates[1][1])
    else:
        footer_features[3].x=0

# create initial display
displayHeader()
lines = loadBody()
footer_features = loadFooter()
display.show(group)

# update the data every 30 seconds
while True:
    try:
        data = fetchData(network)
        display_data = data[:number_trains]
        updateBody(display_data, lines)
        updateFooter(data, footer_features)
        display.show(group)
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        continue

    time.sleep(30)
