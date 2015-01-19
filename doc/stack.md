# Scribbler Stack

## Web application

Communication: HTTP

### Client

Language: Javascript  
Location: browser

- Controls the user interface.
- Synchronizes with the server.
- Enables and disable buttons.
- Shows messages in the console.

### Server

Language: Python  
Location: server machine

- Responds to requests.
- Checks whitelist and open files.
- Creates HTTP headers.

### Communication

- The Client sends GET requests and POST requests to the Server. The Server responds to these requests.
- GET requests are for HTML, CSS, and other resources.
- POST requests are instructions that get passed down the stack to a certain point, and then the response goes back up to the Server and then to the Client.

## Glue

Communication: call/return

### Controller

Language: Python  
Location: server machine

- Runs the Program's main loop.
- Switches, starts, stops, and resets Programs.
- Passes commands down to the robot Program.
- Schedules Greenlets.
- Queues upstream messages.

### Communication

- The Controller receives switch/start/stop/reset messages, robot commands, and synchronization requests from the Server.
- The controller instructs the robot by passing messages to the Program. A status gets sent back, and the Controller passes this up the stack to be displayed in the Client console.
- The main loop occasionally produces voluntary status updates, and the Controller queues these and passes them upstream.

## Robot application

Communication: Bluetooth

### Program

Language: Python  
Location: server machine

- Runs algorithms to control the Robot.
- Contains a main loop function that gets executed continuously.

### Robot

Language: hardware  
Location: real world

- Controls the DC motors and speakers.
- Reads input from the sensors.
- Listens for Bluetooth instructions.

### Communication

- All communication between the Program and the Robot is facilitated by Myro (a Python library).
- Since the Program runs on a computer and not on the Robot itself, there is some latency involved in instructing the Robot.