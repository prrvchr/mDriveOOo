function getParameter(name, value) {
    var parameter = value,
        tmp = [];
    var items = location.search.substr(1).split('&');
    for (var i = 0; i < items.length; i++) {
        tmp = items[i].split('=');
        if (tmp.length === 2 && tmp[0] === name) parameter = decodeURIComponent(tmp[1]);
    }
    return parameter;
}

document.getElementById('user').innerHTML = getParameter('user', '');
