# Udacity Reviewer Activity

It makes a GitHub style activity plot of the daily gains.

![Example](https://github.com/gabraganca/waffle-reviewer/blob/master/random_example.png)

## Dependencies

* requests
* pytz
* NumPy
* pandas
* seaborn

## Usage

Clone this repository or download the `plot_activity.py` script.

```
usage: plot_activity.py [-h] [--auth-token TOKEN] [--debug]

Makes a GitHub style activity plot of daily gains.

optional arguments:
  -h, --help            show this help message and exit
  --auth-token TOKEN, -T TOKEN
                        Your Udacity auth token. To obtain, login to
                        review.udacity.com, open the Javascript console, and
                        copy the output of
                        `JSON.parse(localStorage.currentUser).token`. This can
                        also be stored in the environment variable
                        UDACITY_AUTH_TOKEN.
  --debug, -d           Turn on debug statements.
```

The plot will be saved as `activity.png` in the same directory as the script.

## To do

*  Create and improve the logging messages.
