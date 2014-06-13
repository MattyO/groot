import bottle
import threading

from bottle import template
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication


def get_query_value():
    query = bottle.request.json['query']
    query_value = ''
    if 'value' in query.keys():
        query_value = query['value']
    return query_value

@bottle.get("/ping")
def ping():
    return 'Ping!'


@bottle.post("/click")
def click():
    query_value = get_query_value()
    widget = find_widget(QApplication.topLevelWidgets()[0], query_value)
    if widget is not None:
        QTest.mouseClick(widget, Qt.LeftButton)
        return get_widget_json(widget)
    return {}
        

@bottle.post("/find_element")
def find_element():
    query_value = get_query_value()
    widget = find_widget(QApplication.topLevelWidgets()[0], query_value)
    return get_single_widget_json(widget)


@bottle.get("/ui_tree")
def ui_tree():
    return get_widget_json(QApplication.topLevelWidgets()[0])


def hasmethod(obj, method_name):
    return hasattr(obj, method_name) and callable(getattr(obj, method_name))


def method_or_default(target, method_name, default):
    value  = default
    if hasmethod(target, method_name):
        method = getattr(target, method_name)
        value = method()
    elif hasattr(target, method_name):
        value = getattr(target, method_name)
    return value


def find_widget(parent, query_value):
    for child in parent.children():
        value = method_or_default(child, 'text', '')
        name = method_or_default(child, 'name', '')
        automation_id = method_or_default(child, 'automation_id', '')
        if query_value in value or query_value in name or query_value in automation_id:
            return child

        found_widget = find_widget(child, query_value)
        if found_widget is not None:
            return found_widget

    return None


def get_single_widget_json(widget):
    if widget is None:
        return {}

    widget_id = ''
    win_id = method_or_default(widget, 'effectiveWinId', None)
    if win_id is not None:
        widget_id = "{0}".format(win_id)
    value = method_or_default(widget, 'text', '')
    name = method_or_default(widget, 'name', '')
    x = method_or_default(widget, 'x', 0)
    y = method_or_default(widget, 'y', 0)
    width = method_or_default(widget, 'width', 0)
    height = method_or_default(widget, 'height', 0)
    automation_id = method_or_default(widget, 'automation_id', '')
    is_visible = method_or_default(widget, 'isVisible', False)
    is_enabled = method_or_default(widget, 'isEnabled', False)

    return {'type':widget.__class__.__name__, 'id':widget_id , 'automation_id':automation_id, 'name':name, 'value':value, 'frame':{'x':x,'y':y,'width':width,'height':height}, 'visible':is_visible, 'enabled':is_enabled}


def get_widget_json(widget):
    if widget is None:
        return {}

    widget_json = get_single_widget_json(widget)

    children_json = []
    for child in widget.children():
        children_json.append(get_widget_json(child))
    widget_json['children'] = children_json

    return widget_json


def start_automation_server():
    thread = threading.Thread(target=bottle.run, kwargs={'host':'localhost', 'port':5123, 'quiet':True})
    thread.setDaemon(True)
    thread.start()

