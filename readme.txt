Hi!

To start, run 'pip install requirements' to install all required packages

This chatbot works more like my own little commandline for Weather.

There are some commands below to get information and some ways to make it your own for faster and more accurate data.

Commands:
weather {location} - this will return a 5-day forecast for the location stated.
e.g. - weather london

recommend {location1}, {location2}, {location3} (any number of locations)
This will return a breakdown of the 5-day forcast of all the locations and show clearly which has the most sunny/clear/non-rainy days to avoid the wet weather.
e.g. - recommend london, bristol, cambridge

save {location} {latitude} {longitude}
This will write the location and its co-ordinates to a json file to ensure you are searching the correct place
Rest assured, there is a way to look up the co-ordinates on the app and a one-click solution to copy the command to clipboard.
e.g. save london 51.5085 -0.1257

