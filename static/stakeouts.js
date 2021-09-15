const guildid = document.currentScript.getAttribute('data-guildid');

$(document).ready(function() {
    var factiontable = $('#faction-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: `/bot/stakeouts/${guildid}/1`
        }
    });

    var usertable = $('#user-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: `/bot/stakeouts/${guildid}/0`
        }
    });

    $('#user-table tbody').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#user-modal'));
            modal.show();
        }
        xhttp.open('GET', `/bot/stakeouts/${guildid}/modal?user=${usertable.row(this).data()[0]}`);
        xhttp.send();
    });

    $('#faction-table tbody').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));
            modal.show();
        }
        xhttp.open('GET', `/bot/stakeouts/${guildid}/modal?faction=${factiontable.row(this).data()[0]}`);
        xhttp.send();
    });

    $(document).on('change', '#level', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#user-modal').attr('data-id');

        xhttp.onload = function() {
            usertable.ajax.reload();
        }

        if ($('#level')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=level&user=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=level&user=${id}`);
        }

        xhttp.send();
    });
    
    $(document).on('change', '#status', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#user-modal').attr('data-id');

        xhttp.onload = function() {
            usertable.ajax.reload();
        }

        if ($('#status')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=status&user=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=status&user=${id}`);
        }

        xhttp.send();
    });
    
    $(document).on('change', '#flyingstatus', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#user-modal').attr('data-id');

        xhttp.onload = function() {
            usertable.ajax.reload();
        }

        if ($('#flyingstatus')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=flyingstatus&user=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=flyingstatus&user=${id}`);
        }

        xhttp.send();
    });
    
    $(document).on('change', '#online', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#user-modal').attr('data-id');

        xhttp.onload = function() {
            usertable.ajax.reload();
        }

        if ($('#online')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=online&user=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=online&user=${id}`);
        }

        xhttp.send();
    });
    
    $(document).on('change', '#offline', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#user-modal').attr('data-id');

        xhttp.onload = function() {
            usertable.ajax.reload();
        }

        if ($('#offline')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=offline&user=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=offline&user=${id}`);
        }

        xhttp.send();
    });
    
    $(document).on('change', '#territory', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#faction-modal').attr('data-id');

        xhttp.onload = function() {
            factiontable.ajax.reload();
        }

        if ($('#territory')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=territory&faction=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=territory&faction=${id}`);
        }

        xhttp.send();
    });

    $(document).on('change', '#members', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#faction-modal').attr('data-id');

        xhttp.onload = function() {
            factiontable.ajax.reload();
        }

        if ($('#members')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=members&faction=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=members&faction=${id}`);
        }

        xhttp.send();
    });
    
    $(document).on('change', '#memberstatus', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#faction-modal').attr('data-id');

        xhttp.onload = function() {
            factiontable.ajax.reload();
        }

        if ($('#memberstatus')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=memberstatus&faction=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=memberstatus&faction=${id}`);
        }

        xhttp.send();
    });
    
    $(document).on('change', '#memberactivity', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#faction-modal').attr('data-id');

        xhttp.onload = function() {
            factiontable.ajax.reload();
        }

        if ($('#memberactivity')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=memberactivity&faction=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=memberactivity&faction=${id}`);
        }

        xhttp.send();
    });

    $(document).on('change', '#armory', function() {
        const xhttp = new XMLHttpRequest();
        const id = $('#faction-modal').attr('data-id');

        xhttp.onload = function() {
            factiontable.ajax.reload();
        }

        if ($('#armory')[0].checked) {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=addkey&value=armory&faction=${id}`);
        } else {
            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=removekey&value=armory&faction=${id}`);
        }

        xhttp.send();
    });
});