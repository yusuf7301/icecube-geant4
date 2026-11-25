#ifndef DetectorConstruction_h
#define DetectorConstruction_h 1

#include "G4VUserDetectorConstruction.hh"
#include "G4ThreeVector.hh"
#include "globals.hh"
#include <vector>

class G4VPhysicalVolume;
class G4LogicalVolume;

// IceCube benzeri dedektör: 4 buz katmanı (derinliğe bağlı optik özellikler)
// içine yerleştirilmiş 3x3 string x 4 DOM = 36 optik sensör.
class DetectorConstruction : public G4VUserDetectorConstruction
{
  public:
    DetectorConstruction();
    virtual ~DetectorConstruction();

    virtual G4VPhysicalVolume* Construct();
    virtual void ConstructSDandField(); // Sensörleri hassas dedektör yapar (her thread için)

    // --- Geometri sabitleri ---
    static constexpr G4int kNumStringsX = 3;
    static constexpr G4int kNumStringsY = 3;
    static constexpr G4int kNumDOMs     = 4;  // String başına DOM = buz katmanı sayısı
    static G4int NumSensors() { return kNumStringsX*kNumStringsY*kNumDOMs; }

    static G4double IceHalfSize();      // Buz bloğunun yarı kenarı
    static G4double WorldHalfSize();
    static G4double SensorRadius();
    static G4ThreeVector SensorPosition(G4int sensorID);   // Global konum
    static G4double LayerDepth(G4int layer);               // Katman merkezinin nominal derinliği

    // --- Buzun optik özellikleri (tek kaynak: hem Geant4 hem CSV için) ---
    static G4double IceRefractiveIndex(G4double lambda_nm);        // Faz indisi
    static G4double IceAbsLength(G4double lambda_nm, G4int layer);  // Soğurma uzunluğu
    static G4double IceRayleighLength(G4double lambda_nm, G4int layer);
    static G4double IceMieLength(G4double lambda_nm, G4int layer);      // Geometrik Mie uzunluğu
    static constexpr G4double kMieG = 0.9; // Mie saçılmasında ortalama cos(theta)

    // Sensör konumlarını ve buz özelliklerini analiz için CSV olarak yazar
    static void WriteGeometryCSV(const G4String& prefix);

  private:
    G4LogicalVolume* fLogicSensor = nullptr;
};

#endif
