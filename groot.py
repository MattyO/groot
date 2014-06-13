import bottle
import threading

from bottle import template
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication


@bottle.get("/ping")
def ping():
    return 'Ping!'


@bottle.post("/click")
def click():
    query_value = get_query_value()
    automation_type = get_query_automation_type()
    widget = find_widget(query_value, automation_type)
    if widget is not None:
        QTest.mouseClick(widget, Qt.LeftButton)
        return get_widget_json(widget)
    return {}
        

@bottle.post("/find_element")
def find_element():
    query_value = get_query_value()
    automation_type = get_query_automation_type()
    widget = find_widget(query_value, automation_type)
    return get_single_widget_json(widget)


@bottle.get("/ui_tree")
def ui_tree():
    return get_widget_json(get_root_widget())


def get_query_value():
    query = bottle.request.json['query']
    query_value = ''
    if 'value' in query.keys():
        query_value = query['value']
    return query_value


def get_query_automation_type():
    query = bottle.request.json['query']
    query_value = ''
    if 'automation_type' in query.keys():
        query_value = query['automation_type']
    return query_value


def get_root_widget():
    return QApplication.topLevelWidgets()[0]


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


def find_widget(query_value, automation_type):
    return find_widget_in_parent(get_root_widget(), query_value, automation_type)


def find_widget_in_parent(parent, query_value, automation_type):
    for child in parent.children():
        text = method_or_default(child, 'text', '')
        name = method_or_default(child, 'name', '')
        automation_id = method_or_default(child, 'automation_id', '')
        child_automation_type = method_or_default(child, 'automation_type', '')


        if query_value in text or query_value in name or query_value in automation_id:
            if automation_type is None:
                return child
            elif automation_type in child_automation_type:
                return child

        found_widget = find_widget_in_parent(child, query_value, automation_type)
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
    automation_type = method_or_default(widget, 'automation_type', '')
    is_visible = method_or_default(widget, 'isVisible', False)
    is_enabled = method_or_default(widget, 'isEnabled', False)

    return {'type':widget.__class__.__name__, 'id':widget_id , 'automation_id':automation_id, 'automation_type':automation_type, 'name':name, 'value':value, 'frame':{'x':x,'y':y,'width':width,'height':height}, 'visible':is_visible, 'enabled':is_enabled}


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

