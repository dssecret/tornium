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
    $("#chainform").submit(function(e) {
        e.preventDefault();
        const xhttp = new XMLHttpRequest();
        var value = Number($("#chainff").val());

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response) {
                generateToast("Chain List Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            } else {
                const table = document.querySelector('#chain-table')
                var counter = 1
                response["data"].forEach(function(user) {
                    console.log(user)
                    var tableBody = document.getElementById('chain-table-body');
                    var newNode = document.createElement('tr');
                    newNode.innerHTML = `
                    <tr>
                        <th scope="col">${counter}</th>
                        <th scope="col">${user["battlescore"]}</th>
                        <th scope="col">${user["timeadded"]}</th>
                        <th scope="col">
                            <a href="https://www.torn.com/loader.php?sid=attack&user2ID=${user['tid']}">
                                <i class="fas fa-crosshairs"></i>
                            </a>
                            
                            <a href="https://www.torn.com/profiles.php?XID=${user['tid']}">
                                <i class="fas fa-id-card-alt"></i>
                            </a>
                        </th>
                    </tr>
                    `;
                    tableBody.appendChild(newNode);
                    counter += 1;
                });
            }
        }

        xhttp.responseType = "json";
        xhttp.open("GET", "/api/stat");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'dstats': value
        }));
    });
});
