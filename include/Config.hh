#ifndef Config_h
#define Config_h 1

#include "globals.hh"

class G4GenericMessenger;

// Simülasyonun tüm ayarlarını tutan tekil (singleton) sınıf.
// Değerler makro dosyasından /icecube/... komutlarıyla değiştirilir ve
// her iş parçacığı (thread) aynı değerleri okur.
class Config
{
  public:
    static Config* Instance();

    // Parçacık tabancası
    G4String particle   = "mu-";
    G4double energy;            // Müon kinetik enerjisi
    G4double sourceRA;          // AGN kaynağının sağ açıklığı (RA)
    G4double sourceDec;         // AGN kaynağının dik açıklığı (Dec)
    G4double angularSpread;     // nötrino->müon açısal sapması (1 sigma)
    G4double offsetRadius;      // Müon izinin dedektör merkezinden rastgele kayması

    // Geometri (/run/initialize'dan ÖNCE ayarlanmalı)
    G4double stringSpacing;     // String'ler arası yatay mesafe

    // Çıktı
    G4String prefix     = "data/run"; // CSV dosyalarının ön eki
    G4int    photonSaveEvents = 1;    // Foton CSV'sine yazılacak olay sayısı (dosya çok büyümesin)
    G4bool   saveHitPhotons = true;   // Her sensör fotonunu tek tek yaz (yüksek enerjide kapatılmalı)
    G4bool   saveMuonSteps  = true;   // Müonun her adımını yaz

  private:
    Config();
    ~Config();
    G4GenericMessenger* fMessenger;
};

#endif
