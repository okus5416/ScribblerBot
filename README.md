# Scribbler Bot

Scribbler Bot is a project that we, group 22, are developing for SE 101 in 1A Software Engineering at Waterloo. It is written mainly in Python and uses the [Myro][1] library to control a robot. We are organizing tasks for the project with [Trello boards][2].

[1]: http://wiki.roboteducation.org/Myro_Reference_Manual
[2]: https://trello.com/scribbler22

## Templates

The HTML files for this project (all two of them) are generated from a template, so the first thing you have to do is run that script:

```
python gen-templates.py
```

## Server

Now, you must start the server:

```
python src/main.py
```

Use the `-h` flag to see what other options there are. A particularly useful option is `-d`: this makes the server use a dummy implementation of Myro, allowing you to test the server and web application without the Scribbler Bot.

## Client

The web browser should have opened to `http://localhost:8080` automatically. You control Scribbler Bot via this web app. By clicking the buttons, you can choose a program, start/stop/reset the program, adjust the robot's speed, make it beep, display some information about the robot, clear the console, toggle automatic scrolling of the console, and view and set parameters of the program.

## Object avoidance

When the Avoider program is selected, the Scribbler drives in a straight line until it detects an object. It turns and drives around the object, then continues its path until it encounters another.

## Tracie

Tracie traces shapes. The user draws a polygonal shape in the web application by adding and dragging vertices that are connected by straight lines. The Scribbler receives this data and replicates the drawing as best as it can.

## License

© 2014 Mitchell Kember, Justin Kim, Charles Bai, Leong Si, Renato Zveibil, Min Suk Kim, and Michael Min

Scribbler Bot is available under the MIT License; see [LICENSE](LICENSE.md) for details.