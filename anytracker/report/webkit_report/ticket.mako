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
            <h1>${_("Selected tickets")}</h1>
            <table style="width:100%;">
                <thead>
                    <tr>
                        <th>${_("Number")}</th>
                        <th>${_("Name")}</th>
                        <th>${_("Location")}</th>
                        <th>${_("Rating")}</th>
                        <th>${_("Stage")}</th>
                    </tr>
                </thead>
                <tbody>
                    <% value = 0 %>
                    %for ticket in objects:
                        <tr>
                            <td>${ticket.number}</td>
                            <td>${ticket.name}</td>
                            <td>
                                 ${ticket.breadcrumb}
                            </td>
                            <td>
                                ${ticket.rating}
                                <% value = value + ticket.rating %>
                            </td>
                            <td>
                                 ${ticket.stage_id.name}
                            </td>
                        </tr>
                    %endfor
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="3">
                            ${_("Total")} ${_("Rating")}
                        </td>
                        <td>
                            ${value}
                        </td>
                        <td></td>
                    </tr>
                </tfoot>
            </table>
        </div> <!-- end avoid-page-break -->
    % endif
    %for ticket in objects:
        <div class="page-break-before">
            <h2>
                <span>#${ticket.number}</span>: ${ticket.name}
                <span class="float-right">${_("rating")}: ${ticket.rating}</span>
            </h2>
            <span class="small">${_("Location")}: ${ticket.breadcrumb}</span>
            <span class="small float-right">${_("Stage")}: ${ticket.stage_id.name}</span>
            
            <h3>${_("Description")}</h3>
            % if ticket.description:
                <div> ${ticket.description | n} </div>
            % endif
        </div>  <!-- end breaking page: page-break-before -->
    %endfor
</body>
</html>
