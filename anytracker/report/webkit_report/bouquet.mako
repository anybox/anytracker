## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}
        /*
         * Report css
         */
        
        /*
         * Common css
         *
         * TODO: Move the following section to ir_header_webkit_base_anytracker
         *       to share it between reports
         */


    </style>
</head>
<body>
    % if len(objects) > 1:
        <div class="avoid-page-break">
            <h1>${_("Récapitulatifs des Bouquets")}</h1>
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
                    %for bouquet in objects:
                        <tr>
                            <td>${bouquet.name}</td>
                            <td>
                                % for project in bouquet.project_ids:
                                    <p class="tag">${project.name}</p>
                                % endfor
                            </td>
                            <td>
                                ${bouquet.bouquet_rating}
                                <% value = value + bouquet.bouquet_rating %>
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
    %for bouquet in objects:
        <div class="page-break-before">
            <h1>${bouquet.name}</h1>
            %if bouquet.description:
                <h2>${_("Description")}</h2>
                <p class="std_text"> ${bouquet.description | n} </p>
            %endif
            % if len(bouquet.ticket_ids) > 1:
                <div class="avoid-page-break">
                    <h2>${_("Liste des tickets composant ce bouquet")}</h2>
                    <table>
                      <thead>
                        <tr>
                          <th>
                            ${_("Ticket title")}
                          </th>
                          <th>
                            ${_("Rating")}
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        % for ticket in bouquet.ticket_ids:
                          <tr>
                            <td>
                              ${ ticket.name }
                            </td>
                          </tr>
                        % endfor
                      </tbody>
                      <tfoot>
                        <tr>
                          <td>
                              <th>
                                ${_("Net Total:")}
                              </th>
                              <td>
                                666.66
                              </td>
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                </div>  <!-- end avoid-page-break -->
            % endif
            % for ticket in bouquet.ticket_ids:
                <div class="avoid-page-break">
                    % if len(bouquet.ticket_ids) > 1:
                        <span>${bouquet.name}</span>
                    % endif
                    <h1>${ticket.name}</h1>
                    <span>${ticket.rating}</span>
                    <p>${ticket.description}</p>
                </div>  <!-- end avoid-page-break -->
            % endfor
        </div>  <!-- end breaking page: page-break-before -->
    %endfor
</body>
</html>
