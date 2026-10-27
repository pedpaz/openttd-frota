// IA de vitrine: monta linhas de verdade na maior cidade para os previews.
// Cada companhia pega uma cor, constrói depósito, pontos de ônibus e de caminhão,
// e põe ônibus (passageiros) e caminhões de correio rodando entre os pontos.
class Vitrine extends AIController {
  function Start() {
    local idx = AICompany.ResolveCompanyID(AICompany.COMPANY_SELF);
    local cores = [AICompany.COLOUR_DARK_BLUE, AICompany.COLOUR_GREEN, AICompany.COLOUR_ORANGE, AICompany.COLOUR_PURPLE];
    AICompany.SetPrimaryLiveryColour(AICompany.LS_DEFAULT, cores[idx % cores.len()]);
    AICompany.SetLoanAmount(AICompany.GetMaxLoanAmount());
    AIRoad.SetCurrentRoadType(AIRoad.ROADTYPE_ROAD);
    this.Sleep(20 + idx * 40);

    local towns = AITownList();
    towns.Valuate(AITown.GetPopulation);
    towns.Sort(AIList.SORT_BY_VALUE, false);
    local town = towns.Begin();
    local c = AITown.GetLocation(town);

    local depot = this.Deposito(c);
    AILog.Info("DEPOT " + depot);

    // pontos: drive-through em trecho reto de rua
    local bus = this.Pontos(c, AIRoad.ROADVEHTYPE_BUS, 4, 6);
    local cam = this.Pontos(c, AIRoad.ROADVEHTYPE_TRUCK, 2, 5);
    AILog.Info("PONTOS bus " + bus.len() + " caminhao " + cam.len());

    local motores = {};
    foreach (e, _ in AIEngineList(AIVehicle.VT_ROAD)) {
      if (!AIEngine.IsBuildable(e)) continue;
      motores[AIEngine.GetName(e)] <- e;
    }

    // ônibus: linhas entre pares de pontos
    local regal = this.Achar(motores, "Regal");
    for (local i = 0; i < 6 && bus.len() >= 2; i++) {
      local a = bus[i % bus.len()];
      local b = bus[(i + 1) % bus.len()];
      this.Veiculo(depot, regal, [a, b], AIOrder.OF_NON_STOP_INTERMEDIATE);
    }
    // correio: linha entre os pontos de caminhão
    local mail = this.Achar(motores, "MPS Mail");
    for (local i = 0; i < 2 && cam.len() >= 2; i++) {
      this.Veiculo(depot, mail, [cam[i % 2], cam[(i + 1) % 2]], AIOrder.OF_NON_STOP_INTERMEDIATE);
    }
    // os outros caminhões de 1950 passam pelos pontos de caminhão (só para aparecerem na cidade)
    local outros = ["Balogh Coal", "Witcombe Oil", "Talbott Livestock", "Balogh Goods", "Hereford Grain",
                    "Witcombe Wood", "MPS Iron Ore", "Balogh Steel", "Balogh Armoured"];
    foreach (n in outros) {
      if (cam.len() < 2) break;
      this.Veiculo(depot, this.Achar(motores, n), [cam[0], cam[1]],
                   AIOrder.OF_NON_STOP_INTERMEDIATE | AIOrder.OF_NO_LOAD | AIOrder.OF_NO_UNLOAD);
    }
    AILog.Info("PRONTO");
    while (true) this.Sleep(1000);
  }

  function Achar(motores, trecho) {
    foreach (nome, e in motores) if (nome.find(trecho) != null) return e;
    return null;
  }

  function Deposito(c) {
    local tl = AITileList();
    tl.AddRectangle(c - AIMap.GetTileIndex(6, 6), c + AIMap.GetTileIndex(6, 6));
    tl.Valuate(AIMap.DistanceManhattan, c);
    tl.Sort(AIList.SORT_BY_VALUE, true);
    foreach (t, _ in tl) {
      if (!AIRoad.IsRoadTile(t) || AIRoad.IsRoadStationTile(t)) continue;
      foreach (off in [AIMap.GetTileIndex(1, 0), AIMap.GetTileIndex(-1, 0), AIMap.GetTileIndex(0, 1), AIMap.GetTileIndex(0, -1)]) {
        local d = t + off;
        if (!AITile.IsBuildable(d) || AITile.GetSlope(d) != AITile.SLOPE_FLAT) continue;
        if (AIRoad.BuildRoadDepot(d, t)) { AIRoad.BuildRoad(d, t); return d; }
      }
    }
    return null;
  }

  function Pontos(c, tipo, quantos, distmin) {
    local ret = [];
    local tl = AITileList();
    tl.AddRectangle(c - AIMap.GetTileIndex(9, 9), c + AIMap.GetTileIndex(9, 9));
    tl.Valuate(AIMap.DistanceManhattan, c);
    tl.Sort(AIList.SORT_BY_VALUE, true);
    foreach (t, _ in tl) {
      if (ret.len() >= quantos) break;
      if (!AIRoad.IsRoadTile(t) || AIRoad.IsRoadStationTile(t) || AIRoad.IsRoadDepotTile(t)) continue;
      if (AITile.GetSlope(t) != AITile.SLOPE_FLAT) continue;
      if (AIRoad.GetNeighbourRoadCount(t) != 2) continue;
      local longe = true;
      foreach (p in ret) if (AIMap.DistanceManhattan(p, t) < distmin) longe = false;
      if (!longe) continue;
      foreach (dx in [AIMap.GetTileIndex(1, 0), AIMap.GetTileIndex(0, 1)]) {
        if (!AIRoad.AreRoadTilesConnected(t, t + dx) || !AIRoad.AreRoadTilesConnected(t, t - dx)) continue;
        if (AIRoad.BuildDriveThroughRoadStation(t, t + dx, tipo, AIStation.STATION_NEW)) { ret.append(t); break; }
      }
    }
    return ret;
  }

  function Veiculo(depot, e, paradas, flags) {
    if (e == null) return;
    local v = AIVehicle.BuildVehicle(depot, e);
    AILog.Info("BUILD " + AIEngine.GetName(e) + " -> " + v + " " + AIError.GetLastErrorString());
    if (!AIVehicle.IsValidVehicle(v)) return;
    foreach (p in paradas) AIOrder.AppendOrder(v, p, flags);
    AIVehicle.StartStopVehicle(v);
    this.Sleep(30);
  }
}
