<map version="0.9.0">
<!-- To view this file, download free mind mapping software FreeMind from http://freemind.sourceforge.net -->
<node CREATED="1365168860621" ID="ID_900637744" MODIFIED="1396367904153" TEXT="Droit d&apos;acc&#xe9;s application mlf">
<node CREATED="1365168875658" ID="ID_1748422440" MODIFIED="1365176660650" POSITION="right" TEXT="Worflows g&#xe9;n&#xe9;ral des budgets">
<node CREATED="1365169291516" ID="ID_238176366" MODIFIED="1365169857544" TEXT="Worlflow sur &apos;analytic.budget&apos;">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      Le workflow doit avoir 4 &#233;tape:
    </p>
    <ol>
      <li>
        Brouillon
      </li>
      <li>
        Verrouill&#233; : le passage est effectu&#233; par le personnel de l'ets, et peut &#234;tre bilat&#233;ral
      </li>
      <li>
        Propos&#233; : le passage est effectu&#233; par le proviseur de l'ets. Sur un m&#234;me p&#233;riode, un seul budget peut atteindre cet &#233;tat. Un possiblit&#233; de retour en draft.
      </li>
      <li>
        Accept&#233; : Seul le si&#232;ge peut pousser le workflow jusque cette &#233;tape.
      </li>
    </ol>
  </body>
</html></richcontent>
</node>
</node>
<node CREATED="1365169095173" ID="ID_1463818534" MODIFIED="1396367884153" POSITION="right" TEXT="profils utilisateurs ETS et/ou si&#xe8;ge (atelier)">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      2 groupes principaux : Si&#232;ge et &#201;tablissement
    </p>
    <p>
      Sous groupe:
    </p>
    <p>
      Si&#232;ge:
    </p>
    <p>
      - Administratif technique
    </p>
    <p>
      - Administratif fonctionnel
    </p>
    <p>
      - Supervision du si&#232;ge
    </p>
    <p>
      &#201;tablissement
    </p>
    <p>
      - Responsable
    </p>
    <p>
      - Assistant -&gt; faire encore un sous groupe en dessous de assistant ( comme assistant admistratif, ou assistant gestion, assistant controle de l'enseignement)
    </p>
  </body>
</html></richcontent>
<node CREATED="1365171902831" ID="ID_1538809963" MODIFIED="1365172637819" TEXT="condition de passage de workflow">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      utiliser des ir.rules qui prot&#232;gent les mod&#232;les openerp selon l'etat du workflow. utilisation du champs state pr&#233;c&#233;dement utilis&#233;(voir workflow g&#233;n&#233;ral budget).
    </p>
  </body>
</html></richcontent>
</node>
<node CREATED="1365172033741" ID="ID_988269096" MODIFIED="1365172485328" TEXT="Cr&#xe9;er un abstract model de protection de model">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      les r&#233;gles de securit&#233; par default OpenERP ne permettent pas d'&#233;diter les record a travers les vue form
    </p>
  </body>
</html></richcontent>
</node>
</node>
</node>
</map>
