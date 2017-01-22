#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import termios
import fcntl
import threading
import time
import random


class TState:
    live = True

    @classmethod
    def check(self):
        if not TState.live:
            sys.exit()


def sleep(t):
    dt = 100
    for x in xrange(int(t * dt)):
        TState.check()
        time.sleep(1. / dt)
    TState.check()


def utf(s, to_utf=True):
    if isinstance(s, unicode) and to_utf is False:
        return s.encode('utf8')
    if isinstance(s, str) and to_utf is True:
        return s.decode('utf8')
    if isinstance(s, unicode) and to_utf is True or \
       isinstance(s, str) and to_utf is False:
        return s
    return '{}'.format(s)


class KeyEvent:
    def __init__(self, positioner):
        self.positioner = positioner
        os.system('setterm -cursor off')
        self.fd = sys.stdin.fileno()
        self.oldterm = termios.tcgetattr(self.fd)
        newattr = termios.tcgetattr(self.fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(self.fd, termios.TCSANOW, newattr)

        self.oldflags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags | os.O_NONBLOCK)
        self.__events = {}
        self.run()

    def callback(self, key, function, params=None):
        self.__events[key] = (function, params)

    def rm_callback(self, key):
        if key not in self.__events.keys():
            return False
        del self.__events[key]
        return True

    def watcher(self):
        os.system('setterm -cursor off')
        try:
            while True:
                sleep(0.01)
                try:
                    c = sys.stdin.read(1)
                    if c.isdigit():
                        c = int(c)
                    fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags | os.O_NONBLOCK)
                    if c in self.__events.keys():
                        funk = self.__events[c][0]
                        params = self.__events[c][1]
                        funk(params)
                        del self.__events[c]
                    else:
                        self.__key_event = c
                except IOError:
                    pass
        finally:
            self.paramsBack()

    def paramsBack(self):
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.oldterm)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags)
            os.system('setterm -cursor on')

    def run(self):
        t = threading.Thread(target=self.watcher)
        t.start()

    def wait_key_event(self):
        self.__key_event = None
        while self.__key_event is None:
            sleep(0.01)
        key = self.__key_event
        self.__key_event = None
        return key

    def choice(self):
        text = 'Сделай выбор.'
        self.positioner.p(text, self.positioner.size[0] - 2, 3)
        key = self.wait_key_event()
        self.positioner.p(' ' * len(text), self.positioner.size[0] - 2, 3)
        return key

    def wait_any_key(self):
        text = 'Нажми любую клавишу.'
        self.positioner.p(text, self.positioner.size[0] - 2, 3)
        self.wait_key_event()
        self.positioner.p(' ' * len(text), self.positioner.size[0] - 2, 3)


class TextPositioner:
    def __init__(self):
        self.cli_size()
        self.__place = [1, 1]
        self.__indent = [2, 2]
        self.drow_border()

    def p(self, s, x=None, y=None):
        if x is None:
            x = self.__place[0] + self.__indent[0]
        if y is None:
            y = self.__place[1] + self.__indent[1]
            self.__place[1] += len(utf(s))

        sys.stdout.write("\x1b7\x1b[{};{}f{}\x1b8".format(x, y, utf(s, False)))
        sys.stdout.flush()

    def drow_border(self):
        """
        1.1--> Y
        |
        V

        X
        """
        self.clear()
        bul, bur, bdl, bdr, bg, bv = '╔', '╗', '╚', '╝', '═', '║'
        x, y = self.size
        self.p(bul, 1, 1)
        self.p(bur, 1, y)

        self.p(bdl, x, 1)
        self.p(bdr, x, y)
        line = bg * (y - 2)
        # up
        self.p(line, 1, 2)
        # down
        self.p(line, x, 2)
        # left
        for b in [1, y]:
            for a in xrange(2, x):
                self.p(bv, a, b)

    def cli_size(self):
        self.size = map(int, os.popen('stty size', 'r').read().split())

    def clear(self):
        print '\x1b[2J'

    def check_free_space(self, word):
        if self.size[1] - self.__place[1] - self.__indent[1] * 2 < 0:
            self.__place = [self.__place[0] + 1, 1]

    def pfs(self, c):
        self.p(c)

    def add_space(self):
        place = self.__place
        self.check_free_space(1)
        if place[0] != self.__place[0]:
            return
        self.pfs(' ')

    def add_paragraph(self):
        self.__place[0] += 1
        self.__place[1] = 1

    def new_page(self):
        self.__place = [1, 1]


class Robot:
    def __init__(self, positioner, watcher):
        self.positioner=positioner
        self.watcher=watcher
        self.last_speech = ''
        self.introduce('robot.txt')  # TODO mv eyes data here
        self.animate()
        self.speech_speed = 0.2
        mouth_coord = (5, 6)
        self.normal_mouth = 'Y'
        self.mouth_coord_abs = [self.positioner.size[i] - self.body_size[i] + mouth_coord[i] - 2 for i in xrange(len(self.positioner.size))]
        eye_r = (4, 4)
        eye_l = (4, 8)
        self.eye_r_coord = [self.positioner.size[i] - self.body_size[i] + eye_r[i] - 2 for i in xrange(len(self.positioner.size))]
        self.eye_l_coord = [self.positioner.size[i] - self.body_size[i] + eye_l[i] - 2 for i in xrange(len(self.positioner.size))]
        self.normal_eye = 'O'

    def introduce(self, robot_file):
        self.get_body(robot_file)
        self.get_body_size()
        x, y = self.positioner.size
        a = x - self.body_size[0] - 1
        b = y - self.body_size[1] - 1
        for i in xrange(len(self.body)):
            self.positioner.p(self.body[i], a + i, b)

    def get_body_size(self):
        self.body_size = [len(self.body), max(map(len, self.body))]

    def get_body(self, robot_file):
        with open(robot_file, 'r') as f:
            self.body = f.read().split('\n')[:-1]

    def animate(self):
        t = threading.Thread(target=self.blinks)
        #t.setDaemon(True)
        t.start()

    def blinks(self):
        close_eye = '-'
        time_close_eye = 0.2

        while True:
            time_open_eye = random.randint(2, 6)
            sleep(time_open_eye)
            self.positioner.p(close_eye, self.eye_r_coord[0], self.eye_r_coord[1])
            self.positioner.p(close_eye, self.eye_l_coord[0], self.eye_l_coord[1])
            sleep(time_close_eye)
            self.positioner.p(self.normal_eye, self.eye_r_coord[0], self.eye_r_coord[1])
            self.positioner.p(self.normal_eye, self.eye_l_coord[0], self.eye_l_coord[1])

    def set_speech_speed(self, speed):
        self.__speech_speed_default = self.speech_speed
        self.speech_speed = speed

    def set_speech_speed_default(self):
        if hasattr(self, '__speech_speed_default'):
            self.speech_speed = self.__speech_speed_default

    def say_add(self, speech):
        self.last_speech += '\n{}'.format(speech)
        self.spelling(self.spelling_list(speech))

    def say(self, speech, wipe=False):
        #self.positioner.p([self.last_speech], 13, 10)
        if self.last_speech != '':
            self.positioner.new_page()
            self.set_speech_speed(0)
            #self.positioner.p([self.last_speech], 13, 10)
            #self.positioner.p(self.spelling_list(self.last_speech, wipe=True), 14, 10)
            self.spelling(self.spelling_list(self.last_speech, wipe=True))
            self.set_speech_speed_default()

        self.positioner.new_page()
        if speech == '':
            return
        self.last_speech = speech
        self.spelling(self.spelling_list(speech))

    def spelling_list(self, text, wipe=False):
        speech_list = []
        for p in utf(text).split('\n'):
            speech_list.append([])
            for w in p.split(' '):
                if wipe is False:
                    speech_list[-1].append(w)
                else:
                    speech_list[-1].append(' ' * len(w))
        #self.positioner.p([self.last_speech], 13, 10)
        #self.positioner.p([text], 14, 10)
        #self.positioner.p([speech_list], 15, 10)
        return speech_list

    def spelling(self, spelling_list):
        #self.positioner.p(self.speech_speed, 12, 10)
        if self.speech_speed != 0:
            self.watcher.callback(' ', self.set_speech_speed, 0)

        for p in spelling_list:
            for w in p:
                self.positioner.check_free_space(len(w))
                if self.speech_speed == 0:
                    # print by word
                    self.positioner.p(w)
                else:
                    for c in w:
                        self.positioner.pfs(c)
                        self.positioner.p(c, self.mouth_coord_abs[0], self.mouth_coord_abs[1])
                        sleep(self.speech_speed)
                    self.positioner.p(self.normal_mouth, self.mouth_coord_abs[0], self.mouth_coord_abs[1])
                self.positioner.add_space()
            self.positioner.add_paragraph()
        self.watcher.rm_callback(' ')
        self.set_speech_speed_default()
        #self.positioner.p(self.speech_speed, 10, 10)
        #self.positioner.p(self.__speech_speed_default, 11, 10)


class Lessons:
    def __init__(self):
        self.positioner = TextPositioner()
        self.watcher = KeyEvent(positioner=self.positioner)
        self.watcher.callback('q', self.end, None)
        self.robot = Robot(positioner=self.positioner, watcher=self.watcher)

    def hello(self):
        self.robot.say('Привет Тима!')
        self.watcher.wait_any_key()


    def lesson_1(self):
        self.robot.say('Давай считать?\n\nнажми:\n1 - если согласен\n0 - что бы выйти')
        res = self.watcher.choice()
        while res not in [0, 1]:
            res = self.watcher.choice()
        if res == 1:
            self.lesson_count_1()

    def lesson_count_1(self):
        self.robot.say('Поcчитай')
        action = '+' if random.randint(0, 1) else '-'
        a, b, res = None, None, None
        if action == '+':
            a = random.randint(0, 9)
            b = random.randint(0, 9 - a)
            res = a + b
        else:
            a = random.randint(0, 9)
            b = random.randint(0, a)
            res = a - b
        self.robot.say_add('{} {} {} = ?'.format(a, action, b))
        inter_choise = self.watcher.choice()
        while inter_choise not in range(10):
            inter_choise = self.watcher.choice()

        if inter_choise == res:
            self.robot.say_add('\nВерно!')
        else:
            self.robot.say_add('\nНеправильно! Ответ {}'.format(res))


        self.watcher.wait_any_key()
        #self.robot.say_add('\nПодсказка...')
        #self.watcher.wait_any_key()
        #count = 0
        #for x in xrange(10):

    def goodbay(self):
        self.robot.say('До свидания!')
        self.watcher.wait_any_key()
        self.end()

    def end(self, *args):
        TState.live = False
        self.positioner.p('', 0, 0)
        self.positioner.clear()
        sys.exit()


if __name__ == '__main__':
    lessons = Lessons()
    lessons.hello()
    lessons.lesson_1()
    lessons.goodbay()
