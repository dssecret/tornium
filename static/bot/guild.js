const guildid = document.currentScript.getAttribute('data-guildid');

$(document).ready(function(){
    $('[data-bs-toggle="tooltip"]').tooltip({
        container: '.list-group'
    });

    $('#stakeoutcategory').on('keypress', function(e) {
        if(e.which === 13) {
            const id = $('#stakeoutcategory').val();
            const xhttp = new XMLHttpRequest();

            xhttp.onload = function() {
                window.location.reload();
            }

            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=category&value=${id}`);
            xhttp.send();
        }
    });
});
