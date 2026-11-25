#include "PrimaryGeneratorAction.hh"
#include "Config.hh"
#include "DetectorConstruction.hh"

#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "Randomize.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction()
  : G4VUserPrimaryGeneratorAction()
{
  fParticleGun = new G4ParticleGun(1); // Her olayda 1 müon
}

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fParticleGun;
}

G4ThreeVector PrimaryGeneratorAction::MuonDirectionFromSource(G4double ra, G4double dec)
{
  // Kaynağın yerel yönü (z yukarı). Dec > 0 olan kaynak ufkun altındadır ->
  // müon Dünya'nın içinden geçip aşağıdan yukarı gelir (IceCube "upgoing" olayları).
  G4double alt = -dec;
  G4double az  = ra;
  G4ThreeVector toSource(std::cos(alt)*std::cos(az), std::cos(alt)*std::sin(az), std::sin(alt));
  return -toSource; // Müon kaynaktan uzaklaşan yönde hareket eder
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent)
{
  Config* cfg = Config::Instance();

  fParticleGun->SetParticleDefinition(
    G4ParticleTable::GetParticleTable()->FindParticle(cfg->particle));
  fParticleGun->SetParticleEnergy(cfg->energy);

  // 1. Kaynak yönü + nötrino->müon açısal sapması (iki boyutlu gauss)
  G4ThreeVector dir = MuonDirectionFromSource(cfg->sourceRA, cfg->sourceDec);
  G4ThreeVector u = dir.orthogonal().unit();
  G4ThreeVector v = dir.cross(u).unit();
  dir = (dir + G4RandGauss::shoot(0., cfg->angularSpread)*u
             + G4RandGauss::shoot(0., cfg->angularSpread)*v).unit();

  // 2. İzin dedektör merkezine göre rastgele kayması (yöne dik bir disk içinde)
  u = dir.orthogonal().unit();
  v = dir.cross(u).unit();
  G4double r   = cfg->offsetRadius * std::sqrt(G4UniformRand());
  G4double phi = twopi * G4UniformRand();
  G4ThreeVector offset = r*std::cos(phi)*u + r*std::sin(phi)*v;

  // 3. Başlangıç noktası: buz bloğunun dışında, dünya hacminin içinde
  G4double startDistance = DetectorConstruction::WorldHalfSize() - 1.0*m;
  fParticleGun->SetParticlePosition(offset - startDistance*dir);
  fParticleGun->SetParticleMomentumDirection(dir);
  fParticleGun->GeneratePrimaryVertex(anEvent);
}
