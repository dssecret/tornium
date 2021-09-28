$(document).ready(function() {
    var table = $('#banking-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/faction/bankingdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 5;
});
