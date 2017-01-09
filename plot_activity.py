#!/usr/bin/env python
"""
Makes a GitHub style activity plot of the daily gains.
"""
import os
import logging
import argparse
from datetime import timedelta
import requests
import pytz
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(format='|%(asctime)s| %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_data(token):
    """Get data of completed reviews.

    Attributes
    ---------
    token: str
        The API token. It can be obtained through the Reviewer's dashboard.

    Returns
    -------
    A list of dictionaries where each dictionary gives information on one
    completed submission.
    """

    base_url = 'https://review-api.udacity.com/api/v1'
    submission_completed = '{}/me/submissions/completed/'.format(base_url)

    headers = {'Authorization': token, 'Content-Length': '0'}

    reviews = requests.get(submission_completed, headers=headers)

    logger.debug(reviews.status_code)
    logger.debug(reviews.json())


    if reviews.status_code == 200 and len(reviews.json()) > 0:
        review_data = reviews.json()
    else:
        review_data = None

    return review_data

def get_daily_gain(data, timezone=pytz.timezone('US/Pacific')):
    """Obtain the daily gain.

    Attributes
    ----------
    data: list
        The list of dictionaries where each dictionary gives information on one
        completed submission. It is the output of the `get_data` function

    timezone: pytz.timezone
        A valid pytz timezone. Default is the Pacific Standard Time, which is
        the one used by Udacity

    Returns
    -------
        A Pandas Series where the indices are the days and the values are the
        total gain in USD of that day. The time zone is the Pacific Standard
        Time.
    """

    date_price_data = np.array([(d['completed_at'], d['price']) for d in data])

    price_series = pd.Series(date_price_data[:, 1].astype(float),
                             index=pd.to_datetime(date_price_data[:, 0]))
    price_series = price_series.sort_index()

    # Convert timezone
    utc = pytz.utc
    price_series = price_series.tz_localize(utc).tz_convert(timezone)


    # Calculate the gain by day
    daily_gain = price_series.groupby(pd.TimeGrouper('D')).sum()

    return daily_gain

def fill_data(timeseries):

    # Fill dates from:
    # - Sunday before the current date minus one year
    # - up to next saturday.

    last_date = timeseries.index.max()

    one_year_date = last_date - timedelta(days=365)

    ## Obtain the sunday beofre the date of one year ago
    starting_date = one_year_date - timedelta(days=one_year_date.weekday()+1)

    ## Calculate next saturday
    saturday_id = 5

    days_ahead = saturday_id - last_date.weekday()
    if days_ahead < 0: # Target day already happened this week
        days_ahead += 7
    ending_date = last_date + timedelta(days_ahead)

    # Fill dates with mising zero
    date_range_index = pd.date_range(starting_date, ending_date)
    date_range_series = pd.Series(0, index=date_range_index)

    timeseries = timeseries.combine_first(date_range_series).fillna(method='ffill')

    return timeseries

def plot_activity(series):
    """Plots the Reviewers' activity"""
    months = series.index.map(lambda x: x.strftime('%b'))
    # Obtain the months for the years' week
    months = months[0:-1:7]
    # replace the repeated months
    current_month = ''
    for n, month in enumerate(months):
        if month == current_month:
            months[n] = ''
        else:
            current_month = month

    fig, ax = plt.subplots()

    sns.heatmap(series.values.reshape(-1,7).T, ax=ax,
                cmap='YlGn', cbar=False, linewidths=1, square=True,
                xticklabels=months,
                yticklabels=['','M', '', 'W', '', 'F', ''])

    ax.xaxis.tick_top()

    plt.savefig('activity.png', bbox_inches='tight')

def main(token):
    review_data = get_data(token)
    daily_gain = get_daily_gain(review_data)
    daily_gain = fill_data(daily_gain)
    plot_activity(daily_gain)


if __name__ == "__main__":
    cmd_parser = argparse.ArgumentParser(description =
	"Makes aGitHub style activity plot of daily gains."
    )
    cmd_parser.add_argument('--auth-token', '-T', dest='token',
	metavar='TOKEN', type=str,
	action='store', default=os.environ.get('UDACITY_AUTH_TOKEN'),
	help="""
            Your Udacity auth token. To obtain, login to review.udacity.com,
            open the Javascript console, and copy the output of
            `JSON.parse(localStorage.currentUser).token`.  This can also be
            stored in the environment variable UDACITY_AUTH_TOKEN.
	"""
    )

    cmd_parser.add_argument('--debug', '-d', action='store_true',
                            help='Turn on debug statements.')

    args = cmd_parser.parse_args()

    if not args.token:
        cmd_parser.print_help()
        cmd_parser.exit()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    main(args.token)
