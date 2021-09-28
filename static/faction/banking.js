const guildid = document.currentScript.getAttribute('key');

$(document).ready(function() {
    var table = $('#banking-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/faction/userbankingdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 5;

    $("#requestform").submit(function(e) {
        e.preventDefault();
        const xhttp = new XMLHttpRequest();
        var value = $("#requestamount").val();
        value = value.toLowerCase();
        var stringvalue = value.replace(",", "");
        value = Number(stringvalue.replace(/[^0-9\.]+/g, ""));

        if (stringvalue.endsWith("k")) {
            value *= 1000;
        } else if (stringvalue.endsWith("m")) {
            value *= 1000000;
        } else if (stringvalue.endsWith("b")) {
            value *= 1000000000;
        }

        xhttp.onload = function() {
            var response = xhttp.response;

            document.getElementById('toast-title').innerHTML = "Banking Request Successfully Sent";
            document.getElementById('toast-body').innerHTML = `Banking Request ${response["id"]} for ${response["amount"]} has been successfully submitted to the server.`

            var toastElList = [].slice.call(document.querySelectorAll('.toast'))
            var toastList = toastElList.map(function (toastEl) {
                return new bootstrap.Toast(toastEl, option)
            })
        }
        xhttp.onerror = function() {
            var response = xhttp.response;

            document.getElementById('toast-title').innerHTML = "Banking Request Failed";
            document.getElementById('toast-body').innerHTML = `The Tornium API server has responded with \"${response["message"]} to the submitted banking request.\"`

            var toastElList = [].slice.call(document.querySelectorAll('.toast'))
            var toastList = toastElList.map(function (toastEl) {
                return new bootstrap.Toast(toastEl, option)
            })
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/banking");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'amount_requested': value,
        }));
    });
});
