## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}
        /*
         * Report css
         */
        

    </style>
</head>
<body>
    % if len(objects) > 1:
        <div class="avoid-page-break">
            <h1>${_("Récapitulatifs des Tickets")}</h1>
            <table style="width:100%;">
                <thead>
                    <tr>
                        <th>${_("Name")}</th>
                        <th>${_("Projects")}</th>
                        <th>${_("Rating")}</th>
                    </tr>
                </thead>
                <tbody>
                    <% value = 0 %>
                    %for ticket in objects:
                        <tr>
                            <td>${ticket.name}</td>
                            <td>
                                 ${ticket.project_id.name}
                            </td>
                            <td>
                                ${ticket.rating}
                                <% value = value + ticket.rating %>
                            </td>
                        </tr>
                    %endfor
                </tbody>
                <tfoot>
                    <tr>
                        <td>
                        </td>
                        <td>
                            ${_("Total")} ${_("Rating")}
                        </td>
                        <td>
                            ${value}
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div> <!-- end avoid-page-break -->
    % endif
    %for ticket in objects:
        <div class="page-break-before">
            <h1>${ticket.name}</h1>
            %if ticket.description:
                <h2>${_("Description")}</h2>
                <span>${ticket.rating}</span>
                <p class="std_text"> ${ticket.description | n} </p>
            %endif
        </div>  <!-- end breaking page: page-break-before -->
    %endfor
</body>
</html>
