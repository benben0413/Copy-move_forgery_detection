import numpy as np
import cv2
import math
import KDtree as kd
import time
from skimage import feature
from sklearn.neighbors import KNeighborsClassifier

def rgb_para_cinza(img):
	'''
	Converte a imagem de RGB para escala de cinza. Eu uso no lugar da funcao do opencv porque ela da pesos diferentes às cores.
	'''
	b,g,r = cv2.split(img)
	return (b // 3 + g // 3 + r // 3)

def diferenca(imgA, imgB):
	'''
	Checa a diferenca entre duas imagens
	'''
	for r in range(rows):
		for c in range(columns):
			if imgA[r, c, 0] != imgB[r, c, 0] or imgA[r, c, 1] != imgB[r, c, 1] or imgA[r, c, 2] != imgB[r, c, 2]:
				orig[r, c] = [255, 255, 255]
			else :
				orig[r, c] = [0, 0, 0]

def gerar_blocos(img):
	'''
	Cria os blocos para calcular o histograma de cada um. Os blocos sao representados apenas pela linha e coluna do pixel mais acima e a esquerda do bloco.
	'''
	r = 0
	while r < rows - b + 1:
		c = 0
		while c < columns - b + 1:
			yield (r, c)
			c += espaco
		r += espaco

def gerar_histograma(lbps, lbpMax):
	'''
	Gera um histograma de um conjunto de LBPs
	'''
	histograma = np.zeros(lbpMax + 1, dtype=int)
	for lbp in lbps:
		histograma[int(lbp)] += 1
	return histograma

def num_blocos():
	return ((rows - b) // espaco + 1) * ((columns - b) // espaco + 1) 

def gerar_histograma_blocos(img, lbps, lbpMax):
	'''
	Gera histogramas de todos os blocos nos quais as imagens foram divididas
	'''
	saida = np.zeros((num_blocos(), lbpMax + 1))
	i = 0
	for (r, c) in gerar_blocos(img):
		lista = np.zeros(b*b, dtype=int)
		j = 0
		for x in range(r, r+b):
			for y in range(c, c+b):
				lista[j] = lbps[x, y]
				j += 1
		saida[i] = gerar_histograma(lista, lbpMax)
		i += 1
	return saida

def knn(vetores, pixelsBloco):
	'''
	Obtem o vizinho mais proximo (que nao seja ele mesmo) de cada histograma
	'''
	saida = np.zeros(len(vetores), dtype=int)

	neigh = KNeighborsClassifier(n_neighbors=1)
	for i in range(len(vetores)):
		vetor = np.copy(vetores[i])
		vetores[i] = np.array([100 for _ in vetores[i]])
		neigh.fit(vetores, np.array([x for x in range(len(vetores))]))
		saida[i] = neigh.predict([vetor])
		vetores[i] = vetor
	
	return saida

def identificar(vA, vB, vC):
	'''
	Identifica os blocos copiados e nao copiados
	'''
	saidaA = np.zeros(len(vA), dtype=bool)
	saidaB = np.zeros(len(vA), dtype=bool)
	saidaC = np.zeros(len(vA), dtype=bool)
	saidaD = np.zeros(len(vA), dtype=bool)
	
	for i in range(len(vA)):
		if vA[i] == vB[i] or vB[i] == vC[i] or vC[i] == vA[i]:
			saidaA[i] = True
			if vA[i] == vB[i]:
				saidaB[vA[i]] = True
			else:
				saidaB[vC[i]] = True
		if vA[i] == vB[i] and vA[i] == vC[i]:
			saidaC[i] = True
			saidaD[vA[i]] = True
	return (saidaA, saidaB, saidaC, saidaD)

def identificar2(vA, vB, vC):
	'''
	Identifica os blocos copiados, diferenciando entre original e copia, embora nao possa dizer qual e qual
	'''
	saidaA = np.zeros(len(vA), dtype=bool)
	saidaB = np.zeros(len(vA), dtype=bool)
	saidaC = np.zeros(len(vA), dtype=bool)
	saidaD = np.zeros(len(vA), dtype=bool)
	
	for i in range(len(vA)):
		if vA[i] == vB[i] or vB[i] == vC[i] or vC[i] == vA[i]:
			if not saidaB[i]:
				saidaA[i] = True
				if vA[i] == vB[i]:
					saidaB[vA[i]] = True
				else:
					saidaB[vC[i]] = True
		if vA[i] == vB[i] and vA[i] == vC[i]:
			if not saidaD[i]:
				saidaC[i] = True
				saidaD[vA[i]] = True
	return (saidaA, saidaB, saidaC, saidaD)

def editar(img, blocos):
	'''
	Deixa todos os blocos na imagem copiados pretos
	'''
	i = 0
	saida = np.copy(img)
	for (r, c) in gerar_blocos(img):
		if blocos[i]:
			saida[r:r+b, c:c+b] = [0, 0, 0]
		i += 1
	return saida

def editar2(img, blocosA, blocosB):
	'''
	Deixa um conjunto de blocos na imagem azul e outro verde
	'''
	i = 0
	saida = np.copy(img)
	for (r, c) in gerar_blocos(img):
		if blocosA[i]:
			saida[r:r+b, c:c+b] = [255, 0, 0]
		if blocosB[i]:
			saida[r:r+b, c:c+b] = [0, 255, 0]
		i += 1
	return saida

tempo = time.time()
orig = cv2.imread("Original.bmp")
img = cv2.imread("Original.bmp")
cinza = rgb_para_cinza(img)
b = 3
espaco = 3
(rows, columns) = cinza.shape
print("Experimento com b = " + str(b) + ", espaco = " + str(espaco))

tempoDiff = time.time()
diferenca(orig, img)
print("Tempo de calculo da diferenca real: " + str(time.time() - tempoDiff))

tempoLBP = time.time()
lbpA = feature.local_binary_pattern(cinza, 8, 1, method="nri_uniform")
lbpB = feature.local_binary_pattern(cinza, 12, 2, method="nri_uniform")
lbpC = feature.local_binary_pattern(cinza, 16, 2, method="uniform")
print("Tempo de calculo do LBP: " + str(time.time() - tempoLBP))

tempoHist = time.time()
histogramaA = gerar_histograma_blocos(cinza, lbpA, 8 * (8-1) + 2)
histogramaB = gerar_histograma_blocos(cinza, lbpB, 12 * (12-1) + 2)
histogramaC = gerar_histograma_blocos(cinza, lbpC, 16 + 1)
print("Tempo de geracao dos histogramas: " + str(time.time() - tempoHist))
print("Num. de histogramas: " + str(num_blocos()))

tempoKnn = time.time()
proximosA = knn(histogramaA, b*b)
print("Tempo de calculo do KNN A: " + str(time.time() - tempoKnn))
tempoKnnB = time.time()
proximosB = knn(histogramaB, b*b)
print("Tempo de calculo do KNN B: " + str(time.time() - tempoKnnB))
tempoKnnC = time.time()
proximosC = knn(histogramaC, b*b)
print("Tempo de calculo do KNN C: " + str(time.time() - tempoKnnC))
print("Tempo de calculo do KNN: " + str(time.time() - tempoKnn))

tempoId = time.time()
(idA, idB, idC, idD) = identificar(proximosA, proximosB, proximosC)
(idA2, idB2, idC2, idD2) = identificar2(proximosA, proximosB, proximosC)
print("Tempo de identificacao de copias: " + str(time.time() - tempoId))

tempoEdit = time.time()
imgA = editar(img, idA)
imgB = editar(img, idB)
imgC = editar(img, idC)
imgD = editar(img, idD)
imgA2 = editar2(img, idA2, idB2)
imgB2 = editar2(img, idC2, idD2)
print("Tempo de edicao: " + str(time.time() - tempoEdit))

print("Tempo de Execucao: " + str(time.time() - tempo))

cv2.imshow("Copia A - min. 2", imgA)
cv2.imshow("Copia B - min. 2", imgB)
cv2.imshow("Copia A - min. 3", imgC)
cv2.imshow("Copia B - min. 3", imgD)
cv2.imshow("Copia e Original - min. 2", imgA2)
cv2.imshow("Copia e Original - min. 3", imgB2)
cv2.imshow("Diferenca real", orig)
cv2.waitKey(0)
cv2.destroyAllWindows()
