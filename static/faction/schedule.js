/* This file is part of Tornium.
Tornium is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
Tornium is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with Tornium.  If not, see <https://www.gnu.org/licenses/>. */

const key = document.currentScript.getAttribute('data-key');

$(document).ready(function() {
    var table = $('#schedule-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/faction/scheduledata"
        }
    });

    $('#schedule-table tbody').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#schedule-modal'));
            modal.show();
            
            xhttp = new XMLHttpRequest();
            
            xhttp.onload = function() {
                createWatcherTimeline(this.responseText);
            }
            xhttp.open('GET', '/faction/schedule?uuid=' + table.row(this).data()[0] + '&watchers=True');
            xhttp.send();
        }
        xhttp.open('GET', '/faction/schedule?uuid=' + table.row(this).data()[0]);
        xhttp.send();
    })

    $('#create-schedule').click(function() {
        const xhttp = new XMLHttpRequest();
        var value = $("#requestamount").val();

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response) {
                generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted banking request.\"`);
            } else {
                generateToast("Request Successful", `Banking Request ${response["id"]} for ${response["amount"]} has been successfully submitted to the server.`);
            }

            $('#schedule-table').reload()
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/schedule");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'amount_requested': value,
        }));
    })
});
