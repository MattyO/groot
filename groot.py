import bottle
import threading

from bottle import template
from PyQt5.QtCore import Qt, QPoint, QObject, QMetaObject
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQuick import QQuickItem
from PyQt5.QtQuickWidgets import QQuickWidget


@bottle.get("/ping")
def ping():
    if len(QApplication.topLevelWidgets()) == 0:
        bottle.abort(503, "Still booting up, try again later")

    return 'Ping!'


@bottle.post("/click")
def click():
    window_name = get_window_name()
    query_value = get_query_value()
    automation_type = get_query_automation_type()
    widget = find_widget(window_name, query_value, automation_type)

    if widget is None:
        return {}

    if isinstance(widget, QWidget):
        QTest.mouseClick(widget, Qt.LeftButton)
        return get_widget_json(widget)

    if isinstance(widget, QQuickItem):
        pointf = widget.mapToScene(QPoint(0, 0))
        point = pointf.toPoint()
        x = point.x()
        y = point.y()
        x += widget.width() / 2
        y += widget.height() / 2
        QTest.mouseClick(get_root_widget(), Qt.LeftButton, Qt.NoModifier, point )
        return get_widget_json(widget)

    return {}
        

@bottle.post("/find_element")
def find_element():
    window_name = get_window_name()
    query_value = get_query_value()
    automation_type = get_query_automation_type()
    widget = find_widget(window_name, query_value, automation_type)
    return get_single_widget_json(widget)


@bottle.get("/ui_tree")
def ui_tree():
    return get_widget_json(QApplication.topLevelWidgets()[0])


def get_query_value():
    query = bottle.request.json['query']
    query_value = ''
    if 'value' in query.keys():
        query_value = query['value']
    return query_value

def get_window_name():
    query = bottle.request.json['query']
    window_name = ''
    if 'window_name' in query.keys():
        window_name = query['window_name']
    return window_name

def get_query_automation_type():
    query = bottle.request.json['query']
    query_value = ''
    if 'automation_type' in query.keys():
        query_value = query['automation_type']
    return query_value


def get_root_widget(window_name):
    for top_level_widget in QApplication.topLevelWidgets():
        automation_id = method_or_default(top_level_widget, "automation_id", '')
        if window_name == automation_id:
            return top_level_widget

    return QApplication.topLevelWidgets()[0]


def get_children_for_widget(widget):
    children = None

    if isinstance(widget, QQuickWidget):
        child = method_or_default(widget, "rootObject", None)
        if child is not None:
            children = [child]

    if children is None:
        children = method_or_default(widget, "childItems", None)

    if children is None and hasmethod(widget, "findChildren"):
        try:
            children = widget.findChildren(QObject)
        except Exception as e:
            pass

    if children is None:
        children = []

    return children


def hasmethod(obj, method_name):
    return hasattr(obj, method_name) and callable(getattr(obj, method_name))

def qml_method_or_default(target, method_name, default):
    value = default

    meta_object = target.metaObject()
    index = meta_object.indexOfProperty(method_name)
    if index >= 0:
        value = meta_object.property(index).read(target)

    return value

def method_or_default(target, method_name, default):
    value = default
    if hasmethod(target, method_name):
        method = getattr(target, method_name)
        try:
            value = method()
        except Exception as e:
            pass

    elif hasattr(target, method_name):
        value = getattr(target, method_name)
    return value


def find_widget(window_name, query_value, automation_type):
    return find_widget_in_parent(get_root_widget(window_name), query_value, automation_type)


def find_widget_in_parent(parent, query_value, automation_type):
    for child in get_children_for_widget(parent):
        if is_found_widget(child, query_value, automation_type):
            return child

        found_widget = find_widget_in_parent(child, query_value, automation_type)
        if found_widget is not None:
            return found_widget

    return None

def is_found_widget(widget, query_value, automation_type):
    if isinstance(widget, QQuickItem):
        text = qml_method_or_default(child, 'text', '')
        name = qml_method_or_default(child, 'name', '')
        object_name = qml_method_or_default(child, 'objectName', '')
        automation_id = qml_method_or_default(child, 'automation_id', '')
        child_automation_type = qml_method_or_default(child, 'automation_type', '')
    else:
        text = method_or_default(child, 'text', '')
        name = method_or_default(child, 'name', '')
        object_name = method_or_default(child, 'objectName', '')
        automation_id = method_or_default(child, 'automation_id', '')
        child_automation_type = method_or_default(child, 'automation_type', '')

    if query_value in text or query_value == name or query_value == object_name or query_value == automation_id:
        if automation_type is None:
            return true
        elif automation_type in child_automation_type:
            return true

    return false

def get_single_widget_json(widget):
    if widget is None:
        return {}

    if isinstance(widget, QQuickItem):
        return get_single_qml_item_json(widget)
    else:
        return get_single_qwidget_json(widget)

def get_single_qml_item_json(widget):
    widget_id = ''
    win_id = method_or_default(widget, 'effectiveWinId', None)
    if win_id is not None:
        widget_id = "{0}".format(win_id)
    value = qml_method_or_default(widget, 'text', '')
    name = qml_method_or_default(widget, 'name', None)
    if name is None:
        name = qml_method_or_default(widget, 'objectName', '')

    x = qml_method_or_default(widget, 'x', 0)
    y = qml_method_or_default(widget, 'y', 0)
    width = qml_method_or_default(widget, 'width', 0)
    height = qml_method_or_default(widget, 'height', 0)
    automation_id = method_or_default(widget, 'automation_id', '')
    automation_type = method_or_default(widget, 'automation_type', '')
    is_visible = qml_method_or_default(widget, 'visible', False)
    is_enabled = qml_method_or_default(widget, 'enabled', False)

    return {'type':widget.__class__.__name__, 'id':widget_id , 'automation_id':automation_id, 'automation_type':automation_type, 'name':name, 'value':value, 'frame':{'x':x,'y':y,'width':width,'height':height}, 'visible':is_visible, 'enabled':is_enabled}

def get_single_qwidget_json(widget):
    widget_id = ''
    win_id = method_or_default(widget, 'effectiveWinId', None)
    if win_id is not None:
        widget_id = "{0}".format(win_id)
    value = method_or_default(widget, 'text', '')
    name = qml_method_or_default(widget, 'name', None)
    if name is None:
        name = qml_method_or_default(widget, 'objectName', '')
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
    for child in get_children_for_widget(widget):
        children_json.append(get_widget_json(child))
    widget_json['children'] = children_json

    return widget_json


def start_automation_server():
    thread = threading.Thread(target=bottle.run, kwargs={'host':'localhost', 'port':5123, 'quiet':True})
    thread.setDaemon(False)
    thread.start()

