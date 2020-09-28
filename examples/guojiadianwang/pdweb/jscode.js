function encode(value) {
    var key = '密'.charCodeAt(0);
    var str = "";
    for (var i = 0; i < value.length; i++) {
        str += value.charCodeAt(i) ^ key;
        if (i < value.length - 1) {
            str += "%";
        }
    }
    return str;
}