## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}
        /*
         * Report css
         */
        .description {
            min-height: 50px;
            margin-bottom: 30px;
        }

    </style>
</head>
<body>
    % if len(objects) > 1:
        <div class="avoid-page-break">
            <h1>${_("Selected Bouquets")}</h1>
            <h2 style="margin-top: 100px;">${_("Bouquets summary")}</h2>
            <table>
                <thead>
                    <tr>
                        <th>${_("Name")}</th>
                        <th>${_("Projects")}</th>
                        <th>${_("Rating")}</th>
                    </tr>
                </thead>
                <tbody>
                    <% value = 0 %>
                    %for bouquet in objects:
                        <tr>
                            <td>${bouquet.name}</td>
                            <td>
                                % for project in bouquet.project_ids:
                                    <span class="tag">${project.name}</span>
                                % endfor
                            </td>
                            <td class="align-right">
                                ${bouquet.bouquet_rating}
                                <% value = value + bouquet.bouquet_rating %>
                            </td>
                        </tr>
                    %endfor
                </tbody>
                <tfoot>
                    <tr>
                        <th colspan="2" class="align-right">
                            ${_("Total")} ${_("Rating")}
                        </th>
                        <th class="align-right">
                            ${value}
                        </th>
                    </tr>
                </tfoot>
            </table>
        </div> <!-- end avoid-page-break -->
    % endif
    %for bouquet in objects:
        <div class="page-break-before">
            <div class="avoid-page-break">
                <h1>${bouquet.name}</h1>
                % for project in bouquet.project_ids:
                    <span class="small tag">${project.name}</span>
                % endfor
                <span class="small float-right">${_("Rating")}: ${bouquet.bouquet_rating}</span>
                %if bouquet.description:
                    <h2>${_("Bouquet description")}</h2>
                    <p class="description"> ${bouquet.description | n} </p>
                %endif

                % if len(bouquet.ticket_ids) > 1:
                    <h2>${_("Tickets")}</h2>
                    <table>
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
                            %for ticket in bouquet.ticket_ids:
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
                % endif
                %for ticket in bouquet.ticket_ids:
                    <div class="avoid-page-break">
                        <h2>
                            <span>#${ticket.number}</span>: ${ticket.name}
                            <span class="float-right">${_("rating")}: ${ticket.rating}</span>
                        </h2>
                        <span class="small">${_("Location")}: ${ticket.breadcrumb}</span>
                        <span class="small float-right">${_("Stage")}: ${ticket.stage_id.name}</span>
                        
                        <h3>${_("Description")}</h3>
                        <div class="description">
                            % if ticket.description:
                                ${ticket.description | n}
                            % endif
                        </div>
                    </div>  <!-- end avoid-page-break -->
                %endfor
            </div>  <!-- end avoid-page-break -->
        </div>  <!-- end breaking page: page-break-before -->
    %endfor
</body>
</html>
