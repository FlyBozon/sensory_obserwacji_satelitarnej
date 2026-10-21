def getRefl(aot,h2o,o3,rad):
 out = np.zeros(6)
 #Do zrobienia:
 #dodaj recznie do obiektu korAtm parametry AOT550, zawartosc wody w g/cm2 i ozonu w cm w kolumnie atmosfery
 #Wszystko jest opisane w specyfikacji Py6S:
     
 #korAtm.atmos_profile = AtmosProfile.#tu dokoncz
 #korAtm.aot550=#tu dokoncz
 
 #dalej bez zmian
 for bb in range(6):
  band = bb+1
  if band == 6:
   band = 7
  korAtm.wavelength = Wavelength(getattr(PredefinedWavelengths, 'LANDSAT_TM_B' + str(band)))
  korAtm.atmos_corr=AtmosCorr.AtmosCorrLambertianFromRadiance(rad[bb])
  korAtm.run()
  print('kanal'+str(band)+ ' : ' + str(korAtm.outputs.atmos_corrected_reflectance_lambertian))
  np.put(out, bb, korAtm.outputs.atmos_corrected_reflectance_lambertian)
 return out