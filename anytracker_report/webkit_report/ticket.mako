## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}
        /*
         * Specific report css
         */

    </style>
</head>
<body>
    % if len(objects) > 1:
        <div class="avoid-page-break">
            <h1>${_("Selected tickets")}</h1>
            <table style="margin-top:85px">
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
                            <td class="align-right">
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
                        <th colspan="3" class="align-right">
                            ${_("Total")} ${_("Rating")}
                        </th>
                        <th class="align-right">
                            ${value}
                        </th>
                        <th></th>
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
