# Aila: AI for Aula

Aila - A Christmas present for Danish parents: Open source AI to save parents from endless clicking through the Danish school/kindergarten-parent app.

## What's aila?

`aila` is your own AI to understands the nuances of school-parent communication and give you an update of only the absolutely essential information. I get lost in the onslaught of daily messages from the Aula system that mixes really important information from teachers with nice messages about the daily menu and long political discussions between parents on the essentials of bringing up kids in exactly the way they prefer.

Open source LLM, why? Aula contains data that you don't want to upload to any external server. Therefore, it uses a locally running open source large language model. All Aula data will stay private, no Aula data will leave your machine. 

Aula interface: Aila uses the Aula web parser developed by Morten Helmstedt <helmstedt@gmail.com> https://helmstedt.dk/2021/05/aulas-api-en-opdatering/ All credits from this goes to Morten Helmstedt.

## Features (Or Fun Experiments!)
Aila downloads the daily set of messages and posts from Aula, asks your locally running AI for summaries, and flags messages as either containing important information or things that can be ignored.

## Limitations
- Aila is a fun prototype, nothing more. The inteface can very definitely be much improved. Please submit a pull request if you have improvement for the interface.
- While the LMM (default Mistral 7b OpenOrca) is great, it can sometimes get things wrong (perhaps in particular because most Aula posts are in Danish). A larger model (like GPT4) would certainly work better, but we want this to run locally on your machine (no data should leave your machine). As open source LLMs get better (which they do, the current progress is super fast), Aila will of course work better.
- Aila currently reads posts and messages. Information in Aula can be published in more ways, and it would be great to make Aila capable of reading things besides posts and messages.

## Get Started on the Fun

Ready to dive into this experiment? There are no guarantees, it is entirely on you if you want to try Aila out. If this is OK, here's how to get started:

### Prerequisites

You'll need Python if you don't have it already. Python can be installed from [here](https://www.python.org/downloads/).

### Installation

Clone the repo:

`git clone https://github.com/stefansommer/aila.git`

Navigate to the project directory and install the requirements:

`cd aila
pip install -r requirements.txt`

optionally, make a virtual environment before installing:

`cd aila
virtualenv .
pip install -r requirements.txt`

Create a file `userinfo.json` with your Unilogin credentials. The content of the file should look like this:

`{"username": "yourusername", "password": "yourpassword"}`

Go to https://www.aula.dk and log in with the Unilogin method if you are in doubt what is your username and password.

Optionally edit `model_path` in `aila.py` if you already have the LLM downloaded.

### Usage

Run the script:

`python aila.py`

## Contributing

Aila is currently very experimental and could certainly be much improved. You are very welcome to send pull requests.

## License

`aila` is all about sharing and caring. It's under the [MIT License](LICENSE.md) - feel free to use it however you like.

## Acknowledgments

- Thanks to Morten Helmstedt for making the Aula interface.
- Thanks to GPT4 for helping out with the coding
- Thanks to Sommer AI https://www.sommer-ai.dk for supporting the work.

---

Enjoy `aila`, AI to make parenting easier.

Stefan Sommer <sommer@di.ku.dk>
