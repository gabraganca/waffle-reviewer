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

def create_timeseries(starting_date, ending_date, value=0):
    """Create a Pandas Time Series with constant values.

    Attributes
    ----------
    starting_date: str, pandas.tslib.Timestamp
        The first date of the Time Series.

    ending_date: str, pandas.tslib.Timestamp
        The last date of the Time Series.

    value: int,float
        Value to add to new entries. Default is zero.
    """
    timeseries_index = pd.date_range(starting_date, ending_date)
    timeseries = pd.Series(value, index=timeseries_index)

    return timeseries


def fill_week(timeseries, value=0):
    """Fills the time series with values up to end of week (saturday).

    Attributes
    ----------
    timeseries: pandas.Series
        A Pandas Series where the index are datetimes.

    value: int,float
        Value to add to new entries. Default is zero.

    Returns
    ------

    Returns the time series with the week filled.
    """
    last_date = timeseries.index.max()
    saturday_id = 5

    days_ahead = saturday_id - last_date.weekday()
    if days_ahead < 0: # Target day already happened this week
        days_ahead += 7
    ending_date = last_date + timedelta(days_ahead)

    # Create a timeseries with value and the dates to fille the week
    date_range_series = create_timeseries(last_date+timedelta(days=1),
                                          ending_date,
                                          value)

    # Fill the original timeseries
    filled_timeseries = pd.concat([timeseries, date_range_series])

    return filled_timeseries

def fill_year(timeseries, value=0):
    """Fills the time series with values to complete a year

    Attributes
    ----------
    timeseries: pandas.Series
        A Pandas Series where the index are datetimes.

    value: int,float
        Value to add to new entries. Default is zero.

    Returns
    ------

    Returns the time series with the year filled.
    """
    # Obtain firts and last date from timeseries
    first_date = timeseries.index.min()
    last_date = timeseries.index.max()

    one_year_date = last_date - timedelta(days=365)

    ## Obtain the sunday beofre the date of one year ago
    starting_date = one_year_date - timedelta(days=one_year_date.weekday()+1)

    assert starting_date.weekday_name == 'Sunday'


    # Fill dates with mising zero
    date_range_series = create_timeseries(starting_date,
                                          first_date-timedelta(days=1),
                                          value)

    # Fill the original timeseries
    filled_timeseries = pd.concat([date_range_series, timeseries])

    return filled_timeseries

def plot_activity(series, savename='activity.png'):
    """Plots the Reviewers' activity"""
    # Fills the time series
    ## Fill up to next staurday (end of the week)
    series = fill_week(series)
    ### Fill or truncate timeseries to suit the plot
    number_of_days = 371
    if series.shape[0] > number_of_days:
        # truncate to 371 days
        series = series[-number_of_days:]
    elif series.shape[0] < number_of_days:
        # Fill remaing values with zero
        series = fill_year(series)
        assert series.shape[0] == number_of_days

    # Obtain the months for the years' week
    months = series.index.map(lambda x: x.strftime('%b')).tolist()
    n_weekdays = 7
    # Split in weeks
    months = months[::n_weekdays]
    # replace the repeated months
    current_month = ''
    for n, month in enumerate(months):
        if month == current_month:
            months[n] = ''
        else:
            current_month = month

    # Plot
    fig, ax = plt.subplots()

    sns.heatmap(series.values.reshape(-1,n_weekdays).T, ax=ax,
                cmap='YlGn', cbar=False, linewidths=1, square=True,
                xticklabels=months,
                yticklabels=['','M', '', 'W', '', 'F', ''])

    ax.xaxis.tick_top()

    plt.savefig(savename, bbox_inches='tight')

def main(token):
    review_data = get_data(token)
    daily_gain = get_daily_gain(review_data)
    # Missing value are days not worked. So, revenue = 0.
    daily_gain = daily_gain.fillna(0)

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
