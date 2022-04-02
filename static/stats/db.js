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
    var table = $('#stats-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": true,
        "responsive": true,
        "ajax": {
            url: "/stats/dbdata",
            data: function(d) {
                d.minBS = $('#min-bs').val();
                d.maxBS = $('#max-bs').val();
            }
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#stats-table tbody').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#stats-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('stats-modal'));
                modal.dispose();
            }
            
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#stats-modal'));
            modal.show();
        }
        xhttp.open('GET', '/stats/userdata?user=' + table.row(this).data()[0]);
        xhttp.send();
    });

    $('#min-bs').on('change', function() {
        table.ajax.reload();
    });

    $('#max-bs').on('change', function() {
        table.ajax.reload();
    });
});
