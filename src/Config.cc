#include "Config.hh"
#include "G4GenericMessenger.hh"
#include "G4SystemOfUnits.hh"

Config* Config::Instance()
{
  static Config instance;
  return &instance;
}

Config::Config()
  : energy(1.0*TeV),
    sourceRA(77.358*deg),     // TXS 0506+056 (IceCube-170922A blazarı)
    sourceDec(5.693*deg),
    angularSpread(0.5*deg),
    offsetRadius(3.0*m),
    stringSpacing(6.0*m)
{
  fMessenger = new G4GenericMessenger(this, "/icecube/", "IceCube simulasyon ayarlari");

  // Komutlar yalnızca ana thread'de çalışır; işçi thread'ler değerleri doğrudan okur.
  fMessenger->DeclareProperty("particle", particle, "Parcacik turu (mu-, mu+ ...)")
    .SetToBeBroadcasted(false);
  fMessenger->DeclarePropertyWithUnit("energy", "GeV", energy, "Muon kinetik enerjisi")
    .SetToBeBroadcasted(false);
  fMessenger->DeclarePropertyWithUnit("sourceRA", "deg", sourceRA, "AGN kaynagi RA")
    .SetToBeBroadcasted(false);
  fMessenger->DeclarePropertyWithUnit("sourceDec", "deg", sourceDec, "AGN kaynagi Dec")
    .SetToBeBroadcasted(false);
  fMessenger->DeclarePropertyWithUnit("angularSpread", "deg", angularSpread,
                                      "Muon yonundeki gauss sapma (1 sigma)")
    .SetToBeBroadcasted(false);
  fMessenger->DeclarePropertyWithUnit("offsetRadius", "m", offsetRadius,
                                      "Muon izinin merkezden rastgele kaymasi (disk yaricapi)")
    .SetToBeBroadcasted(false);
  fMessenger->DeclareProperty("prefix", prefix, "CSV dosyalarinin on eki (orn. data/1TeV)")
    .SetToBeBroadcasted(false);
  fMessenger->DeclareProperty("photonSaveEvents", photonSaveEvents,
                              "Fotonlari CSV'ye yazilacak olay sayisi")
    .SetToBeBroadcasted(false);
  fMessenger->DeclareProperty("saveHitPhotons", saveHitPhotons,
                              "Sensor fotonlarini tek tek yaz (sensor ozeti her zaman yazilir)")
    .SetToBeBroadcasted(false);
  fMessenger->DeclareProperty("saveMuonSteps", saveMuonSteps, "Muonun her adimini yaz")
    .SetToBeBroadcasted(false);
  fMessenger->DeclarePropertyWithUnit("stringSpacing", "m", stringSpacing,
                                      "String araligi (/run/initialize'dan once)")
    .SetToBeBroadcasted(false)
    .SetStates(G4State_PreInit);
}

Config::~Config()
{
  delete fMessenger;
}
