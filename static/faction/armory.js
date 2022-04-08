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

$(document).ready(function() {
    $("#armory-users-table").DataTable({
        "processing": false,
        "serverSide": false,
        "ordering": false,
        "responsive": true,
    });

    var itemTable = $("#armory-items-table").DataTable({
        "processing": false,
        "serverSide": false,
        "ordering": true,
        "responsive": true,
        "ajax": {
            url: "/faction/armoryitemdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#armory-items-table').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#item-modal'));
            $("#item-table").DataTable({
                "processing": false,
                "serverSide": false,
                "ordering": true,
                "responsive": false
            })
            modal.show();
        }
        xhttp.open('GET', '/faction/armoryitem?tid=' + getTID(itemTable.row(this).data()[0]));
        xhttp.send();
    });
});
