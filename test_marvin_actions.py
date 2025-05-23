#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for all Marvin actions
"""

import datetime
import json
import os

from datetime import date, time, timedelta
from unittest import mock, TestCase

import requests

from bot import Bot
import marvin_actions
import marvin_general_actions

class ActionTest(TestCase):
    """Test Marvin actions"""
    strings = {}

    @classmethod
    def setUpClass(cls):
        with open("marvin_strings.json", encoding="utf-8") as f:
            cls.strings = json.load(f)


    def executeAction(self, action, message):
        """Execute an action for a message and return the response"""
        return action(Bot.tokenize(message))


    def assertActionOutput(self, action, message, expectedOutput):
        """Call an action on message and assert expected output"""
        actualOutput = self.executeAction(action, message)

        self.assertEqual(actualOutput, expectedOutput)


    def assertActionSilent(self, action, message):
        """Call an action with provided message and assert no output"""
        self.assertActionOutput(action, message, None)


    def assertStringsOutput(self, action, message, expectedoutputKey, subkey=None):
        """Call an action with provided message and assert the output is equal to DB"""
        expectedOutput = self.strings.get(expectedoutputKey)
        if subkey is not None:
            if isinstance(expectedOutput, list):
                expectedOutput = expectedOutput[subkey]
            else:
                expectedOutput = expectedOutput.get(subkey)
        self.assertActionOutput(action, message, expectedOutput)


    def assertBBQResponse(self, todaysDate, bbqDate, expectedMessageKey):
        """Assert that the proper bbq message is returned, given a date"""
        url = self.strings.get("barbecue").get("url")
        message = self.strings.get("barbecue").get(expectedMessageKey)
        if isinstance(message, list):
            message = message[1]
        if expectedMessageKey in ["base", "week", "eternity"]:
            message = message % bbqDate

        with mock.patch("marvin_actions.datetime") as d, mock.patch("marvin_actions.random") as r:
            d.date.today.return_value = todaysDate
            r.randint.return_value = 1
            expected = f"{url}. {message}"
            self.assertActionOutput(marvin_actions.marvinTimeToBBQ, "dags att grilla", expected)


    def createResponseFrom(self, directory, filename):
        """Create a response object with contect as contained in the specified file"""
        with open(os.path.join(directory, f"{filename}.json"), "r", encoding="UTF-8") as f:
            response = requests.models.Response()
            response._content = str.encode(json.dumps(json.load(f)))
            return response


    def assertNameDayOutput(self, exampleFile, expectedOutput):
        """Assert that the proper nameday message is returned, given an inputfile"""
        response = self.createResponseFrom("namedayFiles", exampleFile)
        with mock.patch("marvin_actions.requests") as r:
            r.get.return_value = response
            self.assertActionOutput(marvin_actions.marvinNameday, "nameday", expectedOutput)


    def assertJokeOutput(self, exampleFile, expectedOutput):
        """Assert that a joke is returned, given an input file"""
        response = self.createResponseFrom("jokeFiles", exampleFile)
        with mock.patch("marvin_actions.requests") as r:
            r.get.return_value = response
            self.assertActionOutput(marvin_actions.marvinJoke, "joke", expectedOutput)


    def assertSunOutput(self, expectedOutput):
        """Test that marvin knows when the sun comes up, given an input file"""
        response = self.createResponseFrom("sunFiles", "sun")
        with mock.patch("marvin_actions.requests") as r:
            r.get.return_value = response
            self.assertActionOutput(marvin_actions.marvinSun, "sol", expectedOutput)


    def assertPowerPriceOutput(self, exampleFile, timeOfDay,  expectedOutput):
        """Assert that marvin knows the current power price, given an input file and a time (in UTC)"""
        response = self.createResponseFrom("powerPriceFiles", exampleFile)
        with mock.patch("marvin_actions.datetime", wraps=datetime) as d:
            d.datetime.utcnow.return_value = timeOfDay
            with mock.patch("marvin_actions.requests") as r:
                r.get.return_value = response
                self.assertActionOutput(marvin_actions.marvinPowerPrice, "elpris", expectedOutput)


    def testSmile(self):
        """Test that marvin can smile"""
        with mock.patch("marvin_actions.random") as r:
            r.randint.return_value = 1
            self.assertStringsOutput(marvin_actions.marvinSmile, "le lite?", "smile", 1)
        self.assertActionSilent(marvin_actions.marvinSmile, "sur idag?")

    def testWhois(self):
        """Test that marvin responds to whois"""
        self.assertStringsOutput(marvin_actions.marvinWhoIs, "vem är marvin?", "whois")
        self.assertActionSilent(marvin_actions.marvinWhoIs, "vemär")

    def testGoogle(self):
        """Test that marvin can help google stuff"""
        with mock.patch("marvin_actions.random") as r:
            r.randint.return_value = 1
            self.assertActionOutput(
                marvin_actions.marvinGoogle,
                "kan du googla mos",
                "LMGTFY https://www.google.se/search?q=mos")
            self.assertActionOutput(
                marvin_actions.marvinGoogle,
                "kan du googla google mos",
                "LMGTFY https://www.google.se/search?q=google+mos")
        self.assertActionSilent(marvin_actions.marvinGoogle, "du kan googla")
        self.assertActionSilent(marvin_actions.marvinGoogle, "gogool")

    def testExplainShell(self):
        """Test that marvin can explain shell commands"""
        url = "https://explainshell.com/explain?cmd=pwd"
        self.assertActionOutput(marvin_actions.marvinExplainShell, "explain pwd", url)
        self.assertActionOutput(marvin_actions.marvinExplainShell, "can you explain pwd", url)
        self.assertActionOutput(
            marvin_actions.marvinExplainShell,
            "förklara pwd|grep -o $user",
            f"{url}%7Cgrep+-o+%24user")

        self.assertActionSilent(marvin_actions.marvinExplainShell, "explains")

    def testSource(self):
        """Test that marvin responds to questions about source code"""
        self.assertStringsOutput(marvin_actions.marvinSource, "source", "source")
        self.assertStringsOutput(marvin_actions.marvinSource, "källkod", "source")
        self.assertActionSilent(marvin_actions.marvinSource, "opensource")

    def testBudord(self):
        """Test that marvin knows all the commandments"""
        for n, _ in enumerate(self.strings.get("budord")):
            self.assertStringsOutput(marvin_actions.marvinBudord, f"budord #{n}", "budord", f"#{n}")

        self.assertStringsOutput(marvin_actions.marvinBudord,"visa stentavla 1", "budord", "#1")
        self.assertActionSilent(marvin_actions.marvinBudord, "var är stentavlan?")

    def testQuote(self):
        """Test that marvin can quote The Hitchhikers Guide to the Galaxy"""
        with mock.patch("marvin_actions.random") as r:
            r.randint.return_value = 1
            self.assertStringsOutput(marvin_actions.marvinQuote, "ge os ett citat", "hitchhiker", 1)
            self.assertStringsOutput(marvin_actions.marvinQuote, "filosofi", "hitchhiker", 1)
            self.assertStringsOutput(marvin_actions.marvinQuote, "filosofera", "hitchhiker", 1)
            self.assertActionSilent(marvin_actions.marvinQuote, "noquote")

            for i,_ in enumerate(self.strings.get("hitchhiker")):
                r.randint.return_value = i
                self.assertStringsOutput(marvin_actions.marvinQuote, "quote", "hitchhiker", i)

    def testVideoOfToday(self):
        """Test that marvin can link to a different video each day of the week"""
        with mock.patch("marvin_actions.datetime") as dt:
            for d in range(1, 8):
                day = date(2024, 11, 25) + timedelta(days=d)
                dt.date.today.return_value = day
                weekday = day.strftime("%A")
                weekdayPhrase = self.strings.get("video-of-today").get(weekday).get("message")
                videoPhrase = self.strings.get("video-of-today").get(weekday).get("url")
                response = f"{weekdayPhrase} En passande video är {videoPhrase}"
                self.assertActionOutput(marvin_actions.marvinVideoOfToday, "dagens video", response)
        self.assertActionSilent(marvin_actions.marvinVideoOfToday, "videoidag")

    def testHelp(self):
        """Test that marvin can provide a help menu"""
        self.assertStringsOutput(marvin_actions.marvinHelp, "help", "menu")
        self.assertActionSilent(marvin_actions.marvinHelp, "halp")

    def testSayHi(self):
        """Test that marvin responds to greetings"""
        with mock.patch("marvin_actions.random") as r:
            for skey, s in enumerate(self.strings.get("smile")):
                for hkey, h in enumerate(self.strings.get("hello")):
                    for fkey, f in enumerate(self.strings.get("friendly")):
                        r.randint.side_effect = [skey, hkey, fkey]
                        self.assertActionOutput(marvin_actions.marvinSayHi, "hej", f"{s} {h} {f}")
        self.assertActionSilent(marvin_actions.marvinSayHi, "korsning")

    def testLunchLocations(self):
        """Test that marvin can provide lunch suggestions for certain places"""
        locations = ["karlskrona", "goteborg", "angelholm", "hassleholm", "malmo"]
        with mock.patch("marvin_actions.random") as r:
            for location in locations:
                for i, place in enumerate(self.strings.get("lunch").get("location").get(location)):
                    r.randint.side_effect = [0, i]
                    self.assertActionOutput(
                        marvin_actions.marvinLunch, f"mat {location}", f"Ska vi ta {place}?")
            r.randint.side_effect = [1, 2]
            self.assertActionOutput(
                marvin_actions.marvinLunch, "dags att luncha", "Jag är lite sugen på Indiska?")
        self.assertActionSilent(marvin_actions.marvinLunch, "matdags")

    def testStrip(self):
        """Test that marvin can recommend comics"""
        messageFormat = self.strings.get("commitstrip").get("message")
        expected = messageFormat.format(url=self.strings.get("commitstrip").get("url"))
        self.assertActionOutput(marvin_actions.marvinStrip, "lite strip kanske?", expected)
        self.assertActionSilent(marvin_actions.marvinStrip, "nostrip")

    def testRandomStrip(self):
        """Test that marvin can recommend random comics"""
        messageFormat = self.strings.get("commitstrip").get("message")
        expected = messageFormat.format(url=self.strings.get("commitstrip").get("urlPage") + "123")
        with mock.patch("marvin_actions.random") as r:
            r.randint.return_value = 123
            self.assertActionOutput(marvin_actions.marvinStrip, "random strip kanske?", expected)

    def testTimeToBBQ(self):
        """Test that marvin knows when the next BBQ is"""
        self.assertBBQResponse(date(2024, 5, 17), date(2024, 5, 17), "today")
        self.assertBBQResponse(date(2024, 5, 16), date(2024, 5, 17), "tomorrow")
        self.assertBBQResponse(date(2024, 5, 10), date(2024, 5, 17), "week")
        self.assertBBQResponse(date(2024, 5, 1), date(2024, 5, 17), "base")
        self.assertBBQResponse(date(2023, 10, 17), date(2024, 5, 17), "eternity")

        self.assertBBQResponse(date(2024, 9, 20), date(2024, 9, 20), "today")
        self.assertBBQResponse(date(2024, 9, 19), date(2024, 9, 20), "tomorrow")
        self.assertBBQResponse(date(2024, 9, 13), date(2024, 9, 20), "week")
        self.assertBBQResponse(date(2024, 9, 4), date(2024, 9, 20), "base")

    def testNameDayReaction(self):
        """Test that marvin only responds to nameday when asked"""
        self.assertActionSilent(marvin_actions.marvinNameday, "anything")

    def testNameDayRequest(self):
        """Test that marvin sends a proper request for nameday info"""
        with mock.patch("marvin_actions.requests") as r, mock.patch("marvin_actions.datetime") as d:
            d.datetime.now.return_value = date(2024, 1, 2)
            self.executeAction(marvin_actions.marvinNameday, "namnsdag")
            self.assertEqual(r.get.call_args.args[0], "https://api.dryg.net/dagar/v2.1/2024/1/2")

    def testNameDayResponse(self):
        """Test that marvin properly parses nameday responses"""
        self.assertNameDayOutput("single", "Idag har Svea namnsdag")
        self.assertNameDayOutput("double", "Idag har Alfred och Alfrida namnsdag")
        self.assertNameDayOutput("triple", "Idag har Kasper, Melker och Baltsar namnsdag")
        self.assertNameDayOutput("nobody", "Ingen har namnsdag idag")

    def testNameDayError(self):
        """Tests that marvin returns the proper error message when nameday API is down"""
        with mock.patch("marvin_actions.requests.get", side_effect=Exception("API Down!")):
            self.assertStringsOutput(
                marvin_actions.marvinNameday,
                "har någon namnsdag idag?",
                "nameday",
                "error")

    def testJokeRequest(self):
        """Test that marvin sends a proper request for a joke"""
        with mock.patch("marvin_actions.requests") as r:
            self.executeAction(marvin_actions.marvinJoke, "joke")
            self.assertEqual(
                r.get.call_args.args[0],
                "https://api.chucknorris.io/jokes/random?category=dev")

    def testJoke(self):
        """Test that marvin sends a joke when requested"""
        self.assertJokeOutput("joke", "There is no Esc key on Chuck Norris' keyboard, because no one escapes Chuck Norris.")

    def testJokeError(self):
        """Tests that marvin returns the proper error message when joke API is down"""
        with mock.patch("marvin_actions.requests.get", side_effect=Exception("API Down!")):
            self.assertStringsOutput(marvin_actions.marvinJoke, "kör ett skämt", "joke", "error")

    def testSun(self):
        """Test that marvin sends the sunrise and sunset times """
        self.assertSunOutput(
            "Idag går solen upp 7:12 och ner 18:21. Iallafall i trakterna kring BTH.")

    def testSunError(self):
        """Tests that marvin returns the proper error message when joke API is down"""
        with mock.patch("marvin_actions.requests.get", side_effect=Exception("API Down!")):
            self.assertStringsOutput(marvin_actions.marvinSun, "när går solen ner?", "sun", "error")

    def testUptime(self):
        """Test that marvin can provide the link to the uptime tournament"""
        self.assertStringsOutput(marvin_actions.marvinUptime, "visa lite uptime", "uptime", "info")
        self.assertActionSilent(marvin_actions.marvinUptime, "uptimetävling")

    def testStream(self):
        """Test that marvin can provide the link to the stream"""
        self.assertStringsOutput(marvin_actions.marvinStream, "ska mos streama?", "stream", "info")
        self.assertActionSilent(marvin_actions.marvinStream, "är mos en streamer?")

    def testPrinciple(self):
        """Test that marvin can recite some software principles"""
        principles = self.strings.get("principle")
        for key, value in principles.items():
            self.assertActionOutput(marvin_actions.marvinPrinciple, f"princip {key}", value)
        with mock.patch("marvin_actions.random") as r:
            r.choice.return_value = "dry"
            self.assertStringsOutput(marvin_actions.marvinPrinciple, "princip", "principle", "dry")
        self.assertActionSilent(marvin_actions.marvinPrinciple, "principlös")

    def testCommitRequest(self):
        """Test that marvin sends proper requests when generating commit messages"""
        with mock.patch("marvin_actions.requests") as r:
            self.executeAction(marvin_actions.marvinCommit, "vad skriver man efter commit -m?")
            self.assertEqual(r.get.call_args.args[0], "https://whatthecommit.com/index.txt")

    def testCommitResponse(self):
        """Test that marvin properly handles responses when generating commit messages"""
        message = "Secret sauce #9"
        response = requests.models.Response()
        response._content = str.encode(message)
        with mock.patch("marvin_actions.requests") as r:
            r.get.return_value = response
            expected = f"Använd detta meddelandet: '{message}'"
            self.assertActionOutput(marvin_actions.marvinCommit, "commit", expected)

    def testWeatherRequest(self):
        """Test that marvin sends the expected requests for weather info"""
        with mock.patch("marvin_actions.requests") as r:
            self.executeAction(marvin_actions.marvinWeather, "väder")
            for url in ["https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/13/station/65090/period/latest-hour/data.json",
                        "https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/13/codes.json",
                        "https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/15.5890/lat/56.1500/data.json"]:
                self.assertTrue(mock.call(url, timeout=5) in r.get.call_args_list)

    def testWeatherResponse(self):
        """Test that marvin properly parses weather responses"""
        responses = []
        for responseFile in ["station.json", "codes.json", "weather.json"]:
            with open(os.path.join("weatherFiles", responseFile), "r", encoding="UTF-8") as f:
                response = requests.models.Response()
                response._content = str.encode(json.dumps(json.load(f)))
                responses.append(response)

        with mock.patch("marvin_actions.requests") as r:
            r.get.side_effect = responses
            expected = "Karlskrona just nu: 11.7 °C. Inget signifikant väder observerat."
            self.assertActionOutput(marvin_actions.marvinWeather, "väder", expected)

    def testCommitReaction(self):
        """Test that marvin only generates commit messages when asked"""
        self.assertActionSilent(marvin_actions.marvinCommit, "nocommit")


    def testCommitError(self):
        """Tests that marvin sends the proper message when get commit fails"""
        with mock.patch("marvin_actions.requests.get", side_effect=Exception('API Down!')):
            self.assertStringsOutput(
                marvin_actions.marvinCommit,
                "vad skriver man efter commit -m?",
                "commit",
                "error")

    def testMorning(self):
        """Test that marvin wishes good morning, at most once per day"""
        marvin_general_actions.lastDateGreeted = None
        with mock.patch("marvin_general_actions.datetime") as d:
            d.date.today.return_value = date(2024, 5, 17)
            with mock.patch("marvin_general_actions.random") as r:
                r.choice.return_value = "Morgon"
                self.assertActionOutput(marvin_general_actions.marvinMorning, "morrn", "Morgon")
                # Should only greet once per day
                self.assertActionSilent(marvin_general_actions.marvinMorning, "morgon")
                # Should greet again tomorrow
                d.date.today.return_value = date(2024, 5, 18)
                self.assertActionOutput(marvin_general_actions.marvinMorning, "godmorgon", "Morgon")

    def testPowerPriceReaction(self):
        """Test that marvin only reacts to power price requests when asked"""
        self.assertActionSilent(marvin_actions.marvinPowerPrice, "strömmen är dyr idag!")

    def testPowerPriceRequest(self):
        """Test that marvin sends the expected request for power price info"""
        with mock.patch("marvin_actions.datetime", wraps=datetime) as d:
            d.datetime.today.return_value = date(2025, 1, 12)
            with mock.patch("marvin_actions.requests") as r:
                self.executeAction(marvin_actions.marvinPowerPrice, "elpris")
                expectedUrl = self.strings.get("powerprice").get("url").format("2025-01-12")
                self.assertEqual(r.get.call_args.args[0], expectedUrl)

    def testPowerPriceResponse(self):
        """Test that marvin properly parses weather responses"""
        with mock.patch("marvin_actions.random") as r:
            r.randint.return_value = 0
            self.assertPowerPriceOutput("singleAreaResponse", time(12, 1, 0, 0), "Just nu kostar en kWh 1.4007 SEK i SE4.")
            self.assertPowerPriceOutput("singleAreaResponse", time(15, 0, 1, 0), "Just nu kostar en kWh 1.5130 SEK i SE4. Huvva!")
