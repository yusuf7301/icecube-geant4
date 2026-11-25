#ifndef PrimaryGeneratorAction_h
#define PrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ThreeVector.hh"
#include "globals.hh"

class G4ParticleGun;
class G4Event;

// Seçilen AGN kaynağı yönünden gelen müonu buz bloğuna doğru fırlatır.
class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
  public:
    PrimaryGeneratorAction();
    virtual ~PrimaryGeneratorAction();

    virtual void GeneratePrimaries(G4Event*);

    // Gökyüzü koordinatı (RA, Dec) -> müonun hareket yönü.
    // Güney Kutbu yaklaşımı: yükseklik = -Dec, azimut = RA (yerel yıldız zamanı = 0).
    static G4ThreeVector MuonDirectionFromSource(G4double ra, G4double dec);

  private:
    G4ParticleGun* fParticleGun;
};

#endif
