class VitrineInfo extends AIInfo {
  function GetAuthor()      { return "Claude"; }
  function GetName()        { return "Vitrine"; }
  function GetDescription() { return "Constroi um deposito e roda os veiculos de teste"; }
  function GetVersion()     { return 1; }
  function GetDate()        { return "2026-10-27"; }
  function CreateInstance() { return "Vitrine"; }
  function GetShortName()   { return "VITR"; }
  function GetAPIVersion()  { return "13"; }
}
RegisterAI(VitrineInfo());
